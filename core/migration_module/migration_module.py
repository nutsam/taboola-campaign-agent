import logging
import json
import os
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Tuple
from pydantic import ValidationError
from external.api_clients import FacebookApiClient, TaboolaApiClient, ApiException
from core.error_handler import ApiError
from .schema_models import PlatformSchema
from core.file_processor.file_processor import FileProcessor

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MigrationReport:
    """A simple class to hold the results and logs of a migration task."""
    def __init__(self):
        self.successes = []
        self.failures = []
        self.warnings = []
        logging.info("Migration report initialized.")

    def add_success(self, message):
        self.successes.append(message)
        logging.info(f"SUCCESS: {message}")

    def add_failure(self, message, error):
        self.failures.append({'message': message, 'error': str(error)})
        logging.error(f"FAILURE: {message} | Reason: {str(error)}")

    def add_warning(self, message):
        self.warnings.append(message)
        logging.warning(f"WARNING: {message}")

    def __str__(self):
        return f"""
--- Migration Report ---
- Successes: {len(self.successes)}
- Warnings:  {len(self.warnings)}
- Failures:  {len(self.failures)}
------------------------"""

class PlatformAdapter(ABC):
    """Abstract base class for all platform adapters."""
    def __init__(self, api_client, platform_name: str):
        self.api_client = api_client
        self.platform_name = platform_name
        self.schema = self._load_schema()
        self.transformations = {
            'divide_by_100': self._divide_by_100,
            'extract_creative_data': self._extract_creative_data,
            'extract_tweet_creative_data': self._extract_tweet_creative_data
        }

    def _load_schema(self) -> PlatformSchema:
        """Loads and validates the platform-specific schema from a JSON file."""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        schema_path = os.path.join(current_dir, 'schemas', f'{self.platform_name}_schema.json')
        logging.info(f"Loading schema from {schema_path}...")
        try:
            with open(schema_path, 'r') as f:
                schema_data = json.load(f)
            return PlatformSchema.parse_obj(schema_data)
        except (FileNotFoundError, ValidationError, json.JSONDecodeError) as e:
            logging.error(f"Failed to load or validate schema for {self.platform_name}: {e}")
            raise

    @abstractmethod
    def fetch_campaign_data(self, campaign_id: str) -> dict:
        pass
    
    def fetch_campaign_data_from_file(self, file_data: list) -> list:
        """
        Fetch campaign data from uploaded file.
        
        Args:
            file_data: List of campaign dictionaries from file
            
        Returns:
            List of campaign dictionaries
        """
        return file_data

    def _divide_by_100(self, value):
        return value / 100 if value is not None else None

    def _extract_creative_data(self, creatives):
        return [{'photo_url': c.get('image_url'), 'title': c.get('headline')} for c in creatives or []]

    def _extract_tweet_creative_data(self, creatives):
        return [{'photo_url': c.get('media_url'), 'title': c.get('text')} for c in creatives or []]

    def map_to_taboola(self, source_data: dict, report: MigrationReport) -> tuple[dict, list]:
        """Maps source data to Taboola fields using the loaded schema."""
        logging.info(f"Mapping {self.__class__.__name__} fields to Taboola fields...")
        taboola_campaign = {}
        warnings = []
        
        schema_dict = self.schema.dict()

        for taboola_field, mapping_rules in schema_dict.items():
            source_field = mapping_rules.get('source_field')
            default_value = mapping_rules.get('default')
            field_type = mapping_rules.get('field_type', 'string')
            transform_func_name = mapping_rules.get('transform')
            warning = mapping_rules.get('warning')

            value = None
            if source_field and source_field in source_data:
                value = source_data[source_field]

            if transform_func_name and transform_func_name in self.transformations:
                value = self.transformations[transform_func_name](value)
            
            if value is not None:
                try:
                    if field_type == 'integer':
                        value = int(value)
                    elif field_type == 'float':
                        value = float(value)
                    elif field_type == 'boolean':
                        value = bool(value)
                except (ValueError, TypeError) as e:
                    warnings.append(f"Could not cast {taboola_field} to {field_type}. Error: {e}")
                    continue
                taboola_campaign[taboola_field] = value
            elif default_value is not None:
                taboola_campaign[taboola_field] = default_value
            else:
                report.add_warning(f"No value or default found for required field '{taboola_field}'.")

            if warning:
                warnings.append(warning)
        
        logging.info("...Mapping complete.")
        return taboola_campaign, warnings

class FacebookAdapter(PlatformAdapter):
    """Adapter for migrating campaigns from Facebook."""
    def __init__(self, api_client: FacebookApiClient):
        super().__init__(api_client, 'facebook')
        logging.info("FacebookAdapter initialized.")

    def fetch_campaign_data(self, campaign_id: str) -> dict:
        try:
            return self.api_client.get_campaign(campaign_id)
        except ApiError as e:
            # Re-raise ApiError with additional context for migration
            logging.error(f"Schema validation failed for Facebook campaign {campaign_id}: {e}")
            raise ApiError(
                f"Facebook campaign data validation failed: {e}",
                api_name=e.api_name,
                context={
                    "original_error": str(e),
                    "campaign_id": campaign_id,
                    "migration_context": "FacebookAdapter.fetch_campaign_data"
                }
            )
    
    def fetch_campaign_data_from_file(self, file_data: list) -> list:
        """Override to handle Facebook-specific file data processing."""
        logging.info(f"Processing {len(file_data)} Facebook campaigns from file")
        return file_data

class TwitterAdapter(PlatformAdapter):
    """Adapter for migrating campaigns from Twitter."""
    def __init__(self, api_client):
        super().__init__(api_client, 'twitter')
        logging.info("TwitterAdapter initialized.")

    def fetch_campaign_data(self, campaign_id: str) -> dict:
        logging.warning("Fetching from Twitter is a mock. No real API client implemented.")
        return {
            'name': 'Mock Twitter Campaign',
            'total_budget': 5000,
            'account_name': 'Mock Twitter Brand',
            'tweet_creatives': [
                {'media_url': 'http://example.com/tweet_img.jpg', 'text': 'Check out our new product!'}
            ]
        }
    
    def fetch_campaign_data_from_file(self, file_data: list) -> list:
        """Override to handle Twitter-specific file data processing."""
        logging.info(f"Processing {len(file_data)} Twitter campaigns from file")
        return file_data

class MigrationModule:
    """Coordinates the campaign migration process from a source platform to Taboola."""

    def __init__(self, taboola_client: TaboolaApiClient, source_clients: dict):
        self.taboola_client = taboola_client
        self.adapters = {
            'facebook': FacebookAdapter(source_clients.get('facebook')),
            'twitter': TwitterAdapter(source_clients.get('twitter'))
        }
        self.file_processor = FileProcessor()
        logging.info("MigrationModule initialized with platform adapters and file processor.")

    def process_uploaded_file(self, uploaded_file, platform: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Process uploaded file and validate campaign data.
        
        Args:
            uploaded_file: Streamlit uploaded file object
            platform: Source platform name (facebook, twitter, etc.)
            
        Returns:
            Tuple of (validated_campaigns, validation_result)
        """
        try:
            logging.info(f"Processing uploaded file for platform: {platform}")
            
            # Process the uploaded file
            campaign_data = self.file_processor.process_uploaded_file(uploaded_file)
            
            # Validate campaign data using LLM-powered system
            validated_data, validation_result = self.file_processor.validate_campaign_data(campaign_data, platform)
            
            logging.info(f"File processing completed: {len(validated_data)}/{len(campaign_data)} campaigns valid")
            return validated_data, validation_result
            
        except Exception as e:
            logging.error(f"Failed to process uploaded file: {str(e)}")
            raise

    def get_sample_format(self, platform: str) -> Dict[str, Any]:
        """
        Get sample campaign data format for a specific platform.
        
        Args:
            platform: Platform name (facebook, twitter, etc.)
            
        Returns:
            Dictionary with sample campaign structure
        """
        return self.file_processor.get_sample_format(platform)

    def migrate_campaigns_from_file(self, source_platform: str, file_data: list) -> MigrationReport:
        """
        Migrate multiple campaigns from uploaded file data.
        
        Args:
            source_platform: Source platform name (facebook, twitter, etc.)
            file_data: List of campaign dictionaries from uploaded file
            
        Returns:
            MigrationReport with results for all campaigns
        """
        logging.info(f"\n--- Starting Batch Campaign Migration from {source_platform.capitalize()} ({len(file_data)} campaigns) ---")
        report = MigrationReport()
        adapter = self.adapters.get(source_platform.lower())
        
        if not adapter:
            report.add_failure(f"Migration from '{source_platform}' is not supported.", "AdapterNotFound")
            return report
        
        try:
            # Process each campaign in the file
            for i, campaign_data in enumerate(file_data):
                campaign_name = campaign_data.get('name', f'Campaign_{i+1}')
                
                try:
                    logging.info(f"Processing campaign {i+1}/{len(file_data)}: {campaign_name}")
                    
                    # Map campaign data to Taboola format
                    taboola_data, warnings = adapter.map_to_taboola(campaign_data, report)
                    
                    for warning in warnings:
                        report.add_warning(f"Campaign '{campaign_name}': {warning}")
                    
                    # Upload to Taboola
                    self._upload_to_taboola(taboola_data, report)
                    report.add_success(f"Successfully migrated campaign '{campaign_name}'")
                    
                except Exception as e:
                    report.add_failure(f"Failed to migrate campaign '{campaign_name}': {str(e)}", e.__class__.__name__)
                    
        except Exception as e:
            report.add_failure(f"Batch migration failed: {str(e)}", e.__class__.__name__)
        
        logging.info(f"--- Batch Migration Finished --- {report}")
        return report

    def migrate_campaign(self, source_platform: str, campaign_id: str, data_override: dict = None) -> MigrationReport:
        logging.info(f"\n--- Starting Campaign Migration from {source_platform.capitalize()} for campaign ID '{campaign_id}' ---")
        report = MigrationReport()
        adapter = self.adapters.get(source_platform.lower())
        if not adapter:
            report.add_failure(f"Migration from '{source_platform}' is not supported.", "AdapterNotFound")
            return report
        try:
            source_data = adapter.fetch_campaign_data(campaign_id)
            report.add_success(f"Successfully fetched data for campaign '{campaign_id}'.")
            
            taboola_data, warnings = adapter.map_to_taboola(source_data, report)
            if data_override:
                for key, value in data_override.items():
                    if value is None and key in taboola_data:
                        del taboola_data[key]
                    elif value is not None:
                        taboola_data[key] = value

            report.add_success("Successfully mapped fields to Taboola format.")
            for warning in warnings:
                report.add_warning(warning)

            self._upload_to_taboola(taboola_data, report)

        except ApiError as e:
            # Handle schema validation and API errors from source platforms
            if "schema validation" in str(e).lower():
                report.add_failure(
                    f"Campaign data from {source_platform} failed validation. Please check the source campaign configuration.",
                    f"SchemaValidationError: {e}"
                )
            else:
                report.add_failure(f"{source_platform} API error: {e}", e.__class__.__name__)
        except ApiException as e:
            report.add_failure(f"Taboola API returned an error: {e}", e.__class__.__name__)
        except Exception as e:
            report.add_failure(f"A critical error occurred during migration: {e}", e.__class__.__name__)

        logging.info(f"--- Migration Finished --- {report}")
        return report

    def _upload_to_taboola(self, taboola_data: dict, report: MigrationReport):
        """Uses the injected Taboola API client and adds result to the report."""
        try:
            response = self.taboola_client.create_campaign(taboola_data)
            report.add_success(f"Campaign '{response.get('name')}' created in Taboola with ID '{response.get('id')}'.")
        except ApiError as e:
            report.add_failure(f"Failed to create campaign in Taboola: {e}", e.__class__.__name__)
        except ApiException as e:
            report.add_failure(f"Failed to create campaign in Taboola: {e}", e.__class__.__name__)
