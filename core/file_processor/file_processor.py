import pandas as pd
import json
import csv
import logging
from typing import Dict, List, Any, Union, Tuple
from io import StringIO, BytesIO
from core.error_handler import error_handler, ValidationError, DataProcessingError
from .schema_validator import SchemaValidator, ValidationIssue

class FileProcessor:
    """
    Handles file upload and processing for campaign data import.
    Supports CSV, JSON, and Excel formats.
    """
    
    SUPPORTED_FORMATS = ['csv', 'json', 'xlsx', 'xls']
    
    def __init__(self):
        self.schema_validator = SchemaValidator()
        logging.info("FileProcessor initialized with schema validator.")
    
    def process_uploaded_file(self, uploaded_file, file_format: str = None) -> List[Dict[str, Any]]:
        """
        Process uploaded file and return structured campaign data.
        
        Args:
            uploaded_file: Streamlit uploaded file object or file content
            file_format: File format (csv, json, xlsx, xls). Auto-detected if None.
            
        Returns:
            List of campaign dictionaries
            
        Raises:
            ValidationError: If file format is not supported
            DataProcessingError: If file processing fails
        """
        try:
            # Auto-detect format from filename if not provided
            if file_format is None:
                if hasattr(uploaded_file, 'name'):
                    file_format = uploaded_file.name.split('.')[-1].lower()
                else:
                    raise ValidationError("Cannot determine file format. Please specify format.")
            
            # Validate format
            if file_format not in self.SUPPORTED_FORMATS:
                raise ValidationError(
                    f"Unsupported file format: {file_format}. Supported formats: {', '.join(self.SUPPORTED_FORMATS)}"
                )
            
            logging.info(f"Processing file with format: {file_format}")
            
            # Process based on format
            if file_format == 'csv':
                return self._process_csv(uploaded_file)
            elif file_format == 'json':
                return self._process_json(uploaded_file)
            elif file_format in ['xlsx', 'xls']:
                return self._process_excel(uploaded_file)
                
        except (ValidationError, DataProcessingError):
            raise
        except Exception as e:
            error = DataProcessingError(
                f"Failed to process uploaded file: {str(e)}",
                context={
                    "file_format": file_format,
                    "operation": "file_processing"
                },
                original_error=e
            )
            raise error
    
    def _process_csv(self, uploaded_file) -> List[Dict[str, Any]]:
        """Process CSV file and return campaign data."""
        try:
            if hasattr(uploaded_file, 'read'):
                content = uploaded_file.read()
                if isinstance(content, bytes):
                    content = content.decode('utf-8')
                df = pd.read_csv(StringIO(content))
            else:
                df = pd.read_csv(uploaded_file)
            
            # Convert to list of dictionaries
            campaigns = df.to_dict('records')
            
            # Clean data - remove NaN values
            cleaned_campaigns = []
            for campaign in campaigns:
                cleaned_campaign = {k: v for k, v in campaign.items() if pd.notna(v)}
                cleaned_campaigns.append(cleaned_campaign)
            
            logging.info(f"Successfully processed CSV file with {len(cleaned_campaigns)} campaigns")
            return cleaned_campaigns
            
        except Exception as e:
            raise DataProcessingError(
                f"Failed to process CSV file: {str(e)}",
                context={"file_type": "csv"},
                original_error=e
            )
    
    def _process_json(self, uploaded_file) -> List[Dict[str, Any]]:
        """Process JSON file and return campaign data."""
        try:
            if hasattr(uploaded_file, 'read'):
                content = uploaded_file.read()
                if isinstance(content, bytes):
                    content = content.decode('utf-8')
                data = json.loads(content)
            else:
                with open(uploaded_file, 'r') as f:
                    data = json.load(f)
            
            # Ensure data is a list
            if isinstance(data, dict):
                # If single campaign object, wrap in list
                data = [data]
            elif not isinstance(data, list):
                raise ValidationError("JSON file must contain a campaign object or array of campaigns")
            
            logging.info(f"Successfully processed JSON file with {len(data)} campaigns")
            return data
            
        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON format: {str(e)}")
        except Exception as e:
            raise DataProcessingError(
                f"Failed to process JSON file: {str(e)}",
                context={"file_type": "json"},
                original_error=e
            )
    
    def _process_excel(self, uploaded_file) -> List[Dict[str, Any]]:
        """Process Excel file and return campaign data."""
        try:
            if hasattr(uploaded_file, 'read'):
                df = pd.read_excel(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            # Convert to list of dictionaries
            campaigns = df.to_dict('records')
            
            # Clean data - remove NaN values
            cleaned_campaigns = []
            for campaign in campaigns:
                cleaned_campaign = {k: v for k, v in campaign.items() if pd.notna(v)}
                cleaned_campaigns.append(cleaned_campaign)
            
            logging.info(f"Successfully processed Excel file with {len(cleaned_campaigns)} campaigns")
            return cleaned_campaigns
            
        except Exception as e:
            raise DataProcessingError(
                f"Failed to process Excel file: {str(e)}",
                context={"file_type": "excel"},
                original_error=e
            )
    
    def validate_campaign_data(self, campaigns: List[Dict[str, Any]], platform: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Validate campaign data structure using dynamic schema comparison.
        
        Args:
            campaigns: List of campaign dictionaries
            platform: Source platform (facebook, twitter, etc.)
            
        Returns:
            Tuple of (validated_campaigns, schema_comparison_data)
        """
        try:
            # Use dynamic schema validator
            validated_campaigns, validation_issues = self.schema_validator.validate_campaigns_against_schema(campaigns, platform)
            
            if not validation_issues:
                # No issues, return success data
                return validated_campaigns, {
                    "has_issues": False,
                    "success_message": f"✅ All {len(validated_campaigns)} campaigns passed validation successfully!"
                }
            
            # Generate schema comparison summary
            schema_comparison = self.schema_validator.generate_schema_comparison_summary(
                campaigns, validation_issues, platform
            )
            
            if not validated_campaigns:
                raise ValidationError("No valid campaigns found in uploaded file")
                
            logging.info(f"Validation completed: {len(validated_campaigns)}/{len(campaigns)} campaigns valid, {len(validation_issues)} issues found")
            
            return validated_campaigns, {
                "has_issues": True,
                "schema_comparison": schema_comparison
            }
            
        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            raise DataProcessingError(
                f"Campaign validation failed: {str(e)}",
                context={"platform": platform},
                original_error=e
            )
    
    
    def get_sample_format(self, platform: str) -> Dict[str, Any]:
        """
        Return sample campaign data format for a specific platform.
        
        Args:
            platform: Platform name (facebook, twitter, etc.)
            
        Returns:
            Dictionary with sample campaign structure
        """
        samples = {
            'facebook': {
                'name': 'Sample Facebook Campaign',
                'objective': 'LINK_CLICKS',
                'daily_budget': 100.0,
                'targeting': {
                    'geo': 'US',
                    'age_min': 25,
                    'age_max': 65,
                    'interests': ['technology', 'business']
                },
                'creatives': [
                    {
                        'image_url': 'https://example.com/image.jpg',
                        'headline': 'Sample Ad Headline',
                        'description': 'Sample ad description'
                    }
                ]
            },
            'twitter': {
                'name': 'Sample Twitter Campaign',
                'total_budget': 1000.0,
                'account_name': 'Sample Brand',
                'tweet_creatives': [
                    {
                        'media_url': 'https://example.com/tweet_image.jpg',
                        'text': 'Sample tweet content'
                    }
                ]
            }
        }
        
        return samples.get(platform, {
            'name': 'Sample Campaign',
            'budget': 100.0,
            'description': 'Sample campaign description'
        })