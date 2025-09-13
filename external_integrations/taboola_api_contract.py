from abc import ABC, abstractmethod

class ITaboolaApiClient(ABC):
    """
    Defines the contract (interface) for a Taboola API client.
    
    This abstract class serves as a clear to-do list for the developer responsible
    for implementing the real API integration. Any concrete implementation must
    inherit from this class and implement all its abstract methods.
    """

    @abstractmethod
    def connect(self):
        """Handles authentication and connection to the Taboola API."""
        pass

    @abstractmethod
    def create_campaign(self, campaign_data: dict) -> dict:
        """
        Creates a new campaign in Taboola.

        Args:
            campaign_data: A dictionary containing all necessary campaign fields,
                         such as 'name', 'branding_text', 'cpc_bid', etc.

        Returns:
            A dictionary representing the newly created campaign from the API.
        
        Raises:
            ApiException: If the API returns an error (e.g., validation error).
        """
        pass

class ITaboolaHistoricalDataClient(ABC):
    """
    Defines the contract for a client that accesses Taboola's historical
    campaign data warehouse.
    """

    @abstractmethod
    def connect(self):
        """Handles connection to the data warehouse."""
        pass

    @abstractmethod
    def get_similar_campaigns(self, user_campaign_data: dict) -> list[dict]:
        """
        Finds and returns a list of successful, similar campaigns from the warehouse.

        Args:
            user_campaign_data: A dictionary of the user's proposed campaign settings.

        Returns:
            A list of dictionaries, where each dictionary is a historical campaign.
        """
        pass
