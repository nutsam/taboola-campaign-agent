from abc import ABC, abstractmethod
import logging

# Import the contracts that need to be implemented
from .taboola_api_contract import ITaboolaApiClient, ITaboolaHistoricalDataClient

# Custom exception for mock API errors
class ApiException(Exception):
    pass

class ApiClient(ABC):
    """Abstract base class for all API clients."""
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        logging.info(f"{self.__class__.__name__} initialized.")

    @abstractmethod
    def connect(self):
        pass

# --- Third-Party API Clients ---

class FacebookApiClient(ApiClient):
    """(Pseudo-code) Client for the Facebook Ads API."""
    def connect(self):
        logging.info("Connecting to Facebook Ads API...")
        logging.info("   ...Connection successful.")

    def get_campaign(self, campaign_id: str) -> dict:
        logging.info(f"Facebook API: Fetching campaign {campaign_id}...")
        return {
            'name': 'My Awesome FB Campaign',
            'objective': 'LINK_CLICKS',
            'daily_budget': 20.00,
            'targeting': {'geo': 'US', 'age_min': 25, 'interests': ['sports', 'finance']},
            'creatives': [{'image_url': 'http://facebook.com/img.png', 'headline': 'My FB Ad'}]
        }

class TwitterApiClient(ApiClient):
    """(Pseudo-code) Client for the Twitter Ads API."""
    def connect(self):
        logging.info("Connecting to Twitter Ads API...")
        logging.info("   ...Connection successful.")

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

class NlpApiClient(ApiClient):
    """(Pseudo-code) Client for an external NLP service."""
    def connect(self):
        logging.info("Connecting to NLP Service...")
        logging.info("   ...Connection successful.")

    def parse_intent_and_entities(self, user_message: str) -> dict:
        if 'http' in user_message or '.com' in user_message:
            return {'intent': 'provide_url', 'entities': {'url': 'http://my-new-tech-product.com'}}
        elif 'budget' in user_message and any(char.isdigit() for char in user_message):
            return {'intent': 'provide_budget', 'entities': {'budget': int(''.join(filter(str.isdigit, user_message)))}}
        elif 'cpa' in user_message.lower() and any(char.isdigit() for char in user_message):
            return {'intent': 'provide_cpa', 'entities': {'cpa': int(''.join(filter(str.isdigit, user_message)))}}
        elif 'platform' in user_message.lower():
            return {'intent': 'provide_platform', 'entities': {'platform': 'All'}}
        else:
            return {'intent': 'greeting', 'entities': {}}

# --- Taboola API Mock Implementations ---

class TaboolaApiClient(ITaboolaApiClient, ApiClient):
    """(Pseudo-code) Mock implementation of the Taboola API contract."""
    def connect(self):
        logging.info("Connecting to Taboola API...")
        logging.info("   ...Connection successful.")

    def create_campaign(self, campaign_data: dict) -> dict:
        logging.info(f"Taboola API: Validating data for new campaign '{campaign_data.get('name')}'...")
        required_fields = ['name', 'branding_text', 'cpc_bid', 'daily_cap']
        missing_fields = [field for field in required_fields if not campaign_data.get(field)]
        
        if missing_fields:
            raise ApiException(f"Cannot create campaign. Missing required fields: {missing_fields}")

        logging.info("   ...Validation successful. Creating campaign.")
        return {
            'id': 'taboola_campaign_98765',
            'name': campaign_data['name'],
            'branding_text': campaign_data['branding_text'],
            'cpc_bid': campaign_data['cpc_bid'],
            'daily_cap': campaign_data['daily_cap'],
            'status': 'PENDING_APPROVAL'
        }

class TaboolaHistoricalDataClient(ITaboolaHistoricalDataClient, ApiClient):
    """(Pseudo-code) Mock implementation of the Taboola Historical Data contract."""
    def connect(self):
        logging.info("Connecting to Taboola Historical Campaign Data Warehouse...")
        logging.info("   ...Connection successful.")

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