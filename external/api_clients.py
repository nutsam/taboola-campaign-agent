from abc import ABC, abstractmethod
import logging

# Import the contracts that need to be implemented
from .taboola_api_contract import ITaboolaApiClient, ITaboolaHistoricalDataClient
from core.error_handler import error_handler, ApiError

# Custom exception for mock API errors
class ApiException(Exception):
    pass

class ApiClient(ABC):
    """Abstract base class for all API clients."""
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        logging.info(f"{self.__class__.__name__} initialized.")

    @abstractmethod
    def get_campaign(self, campaign_id: str) -> dict:
        pass

# --- Third-Party API Clients ---

class FacebookApiClient(ApiClient):
    """(Pseudo-code) Client for the Facebook Ads API."""
    def get_campaign(self, campaign_id: str) -> dict:
        logging.info(f"Facebook API: Fetching campaign {campaign_id}...")
        
        if campaign_id == "fb-001":
            campaign_data = {
                'name': 'My Awesome FB Campaign',
                'objective': 'LINK_CLICKS',
                'daily_budget': 20.00,
                'targeting': {'geo': 'US', 'age_min': 25, 'interests': ['sports', 'finance']},
                'creatives': [{'image_url': 'http://facebook.com/img.png', 'headline': 'My FB Ad'}]
            }
        else:
            campaign_data = {
                # 'name': 'My Awesome FB Campaign',  # Intentionally missing to trigger validation error
                'objective': 'LINK_CLICKS',
                'daily_budget': -3,  # Intentionally invalid to trigger validation error
                'targeting': {'geo': 'US', 'age_min': 25, 'interests': ['sports', 'finance']},
                'creatives': [{'image_url': 'http://facebook.com/img.png', 'headline': 'My FB Ad'}]
            }
        
        # Validate campaign schema
        self._validate_campaign_schema(campaign_data, campaign_id)
        return campaign_data
    
    def _validate_campaign_schema(self, campaign_data: dict, campaign_id: str):
        """Validate Facebook campaign data schema and raise clear errors if invalid."""
        errors = []
        
        # Check for required fields
        required_fields = ['name', 'objective', 'daily_budget', 'targeting', 'creatives']
        for field in required_fields:
            if field not in campaign_data:
                errors.append(f"Missing required field: '{field}'")
        
        # Validate specific field values
        if 'daily_budget' in campaign_data:
            budget = campaign_data['daily_budget']
            if not isinstance(budget, (int, float)) or budget <= 0:
                errors.append(f"Invalid daily_budget: {budget}. Must be a positive number.")
        
        if 'name' in campaign_data:
            name = campaign_data['name']
            if not isinstance(name, str) or not name.strip():
                errors.append(f"Invalid campaign name: '{name}'. Must be a non-empty string.")
        
        # If there are validation errors, raise a clear ApiError
        if errors:
            error_message = f"Facebook campaign {campaign_id} has schema validation errors: {'; '.join(errors)}"
            error = ApiError(
                error_message,
                api_name="Facebook API",
                context={
                    "campaign_id": campaign_id,
                    "validation_errors": errors,
                    "campaign_data": campaign_data
                }
            )
            error_handler.handle_error(error)
            raise error

class TwitterApiClient(ApiClient):
    """(Pseudo-code) Client for the Twitter Ads API."""
    def get_campaign(self, campaign_id: str) -> dict:
        logging.info(f"Twitter API: Fetching campaign {campaign_id}...")
        return {
            'name': 'My Awesome Twitter Campaign',
            'total_budget': 5000,
            'account_name': 'My Twitter Brand',
            'tweet_creatives': [
                {'media_url': 'http://twitter.com/img.png', 'text': 'My Twitter Ad'}
            ]
        }

# --- Taboola API Mock Implementations ---

class TaboolaApiClient(ITaboolaApiClient):
    """(Pseudo-code) Mock implementation of the Taboola API contract."""
    def create_campaign(self, campaign_data: dict) -> dict:
        try:
            logging.info(f"Taboola API: Validating data for new campaign '{campaign_data.get('name')}'...")
            required_fields = ['name', 'branding_text', 'cpc_bid', 'daily_cap']
            missing_fields = [field for field in required_fields if not campaign_data.get(field)]
            
            if missing_fields:
                error = ApiError(
                    f"Cannot create campaign. Missing required fields: {missing_fields}",
                    api_name="Taboola API",
                    context={"missing_fields": missing_fields, "campaign_data": campaign_data}
                )
                raise error

            logging.info("   ...Validation successful. Creating campaign.")
            return {
                'id': 'taboola_campaign_98765',
                'name': campaign_data['name'],
                'branding_text': campaign_data['branding_text'],
                'cpc_bid': campaign_data['cpc_bid'],
                'daily_cap': campaign_data['daily_cap'],
                'status': 'PENDING_APPROVAL'
            }
        except ApiError:
            raise  # Re-raise our custom errors
        except Exception as e:
            # Convert unexpected errors to ApiError
            error = ApiError(
                f"Unexpected error creating campaign: {str(e)}",
                api_name="Taboola API",
                context={"campaign_data": campaign_data}
            )
            error_handler.handle_error(error)
            raise error

class TaboolaHistoricalDataClient(ITaboolaHistoricalDataClient):
    """(Pseudo-code) Mock implementation of the Taboola Historical Data contract."""
    def get_similar_campaigns(self, user_campaign_data: dict) -> list[dict]:
        category = "Tech"
        logging.info(f"Taboola Warehouse: Querying for successful campaigns in category '{category}'...")
        return [
            {'id': 'tb_101', 'cpc_bid': 0.45, 'daily_cap': 100, 'targeting': {'platform': 'Mobile'}, 'roi': 1.3},
            {'id': 'tb_102', 'cpc_bid': 0.55, 'daily_cap': 150, 'targeting': {'platform': 'Desktop'}, 'roi': 1.8},
        ]

    def get_budget_range(self) -> tuple[float, float]:
        logging.info("Taboola Warehouse: Querying for budget range...")
        return 50.0, 500.0

    def get_cpa_range(self) -> tuple[float, float]:
        logging.info("Taboola Warehouse: Querying for CPA range...")
        return 2.0, 15.0