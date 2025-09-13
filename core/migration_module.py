import logging
import json
from abc import ABC, abstractmethod
from pydantic import ValidationError
from external.api_clients import FacebookApiClient, TaboolaApiClient, ApiException
from .schema_models import PlatformSchema

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
        schema_path = f'core/schemas/{self.platform_name}_schema.json'
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

    def _divide_by_100(self, value):
        return value / 100 if value is not None else None

    def _extract_creative_data(self, creatives):
        return [{'photo_url': c.get('image_url'), 'title': c.get('headline')} for c in creatives or []]

    def _extract_tweet_creative_data(self, creatives):
        return [{'photo_url': c.get('media_url'), 'title': c.get('text')} for c in creatives or []]

    def map_to_taboola(self, source_data: dict) -> tuple[dict, list]:
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
        return self.api_client.get_campaign(campaign_id)

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

class MigrationModule:
    """Coordinates the campaign migration process from a source platform to Taboola."""

    def __init__(self, taboola_client: TaboolaApiClient, source_clients: dict):
        self.taboola_client = taboola_client
        self.adapters = {
            'facebook': FacebookAdapter(source_clients.get('facebook')),
            'twitter': TwitterAdapter(source_clients.get('twitter'))
        }
        logging.info("MigrationModule initialized with platform adapters.")

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
            
            taboola_data, warnings = adapter.map_to_taboola(source_data)
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

        except ApiException as e:
            report.add_failure(f"Taboola API returned an error: {e}", e.__class__.__name__)
        except Exception as e:
            report.add_failure(f"A critical error occurred during migration: {e}", e.__class__.__name__)

        logging.info(f"--- Migration Finished --- {report}")
        return report

    def _upload_to_taboola(self, taboola_data: dict, report: MigrationReport):
        """Uses the injected Taboola API client and adds result to the report."""
        response = self.taboola_client.create_campaign(taboola_data)
        report.add_success(f"Campaign '{response.get('name')}' created in Taboola with ID '{response.get('id')}'.")
