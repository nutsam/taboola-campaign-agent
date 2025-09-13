import logging
from external.api_clients import TaboolaHistoricalDataClient

class DataProcessor:
    """
    Processes and validates user inputs for campaign creation.
    """

    def __init__(self, historical_data_client: TaboolaHistoricalDataClient):
        """
        Initializes the DataProcessor with a historical data client.
        """
        self.historical_data_client = historical_data_client
        logging.info("DataProcessor initialized.")

    def validate_url(self, url: str) -> tuple[bool, str]:
        """
        Validates the URL format.
        Returns (is_valid, feedback_message).
        """
        if not url.startswith("http://") and not url.startswith("https://"):
            return False, "Please provide a valid URL, starting with http:// or https://"
        return True, ""
    
    def validate_budget(self, budget: float) -> tuple[bool, str]:
        """
        Validates the campaign budget against historical data.
        Returns (is_valid, feedback_message).
        """
        min_budget, max_budget = self.historical_data_client.get_budget_range()
        if budget < min_budget:
            return False, f"Your budget of ${budget} is quite low. For similar campaigns, we've seen an average daily budget of ${min_budget}-${max_budget} to be effective."
        if budget > max_budget * 2: # Allow some leeway
            return False, f"Your budget of ${budget} is quite high. While this can lead to high reach, it's significantly above the typical range of ${min_budget}-${max_budget} for similar campaigns. Are you sure about this amount?"
        return True, ""

    def validate_cpa(self, cpa: float) -> tuple[bool, str]:
        """
        Validates the target CPA against historical data.
        Returns (is_valid, feedback_message).
        """
        min_cpa, max_cpa = self.historical_data_client.get_cpa_range()
        if cpa < min_cpa:
            return False, f"Your target CPA of ${cpa} might be too low to be competitive. Similar campaigns have a target CPA in the range of ${min_cpa}-${max_cpa}."
        if cpa > max_cpa:
            return False, f"Your target CPA of ${cpa} is on the higher side. You might be overpaying for acquisitions. The typical range is ${min_cpa}-${max_cpa}."
        return True, ""

    def validate_platform(self, platform: str) -> tuple[bool, str]:
        """
        Validates the target platform.
        Returns (is_valid, feedback_message).
        """
        valid_platforms = ["Desktop", "Mobile", "Both"]
        if platform not in valid_platforms:
            return False, f"Platform '{platform}' is not supported. Please choose from: Desktop, Mobile, or Both."
        return True, ""
