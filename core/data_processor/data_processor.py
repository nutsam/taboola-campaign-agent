import logging
from external.api_clients import TaboolaHistoricalDataClient
from core.error_handler import error_handler, ValidationError

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
        try:
            if not url.strip():
                error = ValidationError("URL cannot be empty", field="url", value=url)
                return False, error_handler.handle_error(error)
                
            if not url.startswith("http://") and not url.startswith("https://"):
                error = ValidationError("URL must start with http:// or https://", field="url", value=url)
                return False, error_handler.handle_error(error)
                
            return True, ""
        except Exception as e:
            error_message = error_handler.handle_error(e, context={"operation": "URL validation", "url": url})
            return False, error_message
    
    def validate_budget(self, budget: float) -> tuple[bool, str]:
        """
        Validates the campaign budget against historical data.
        Returns (is_valid, feedback_message).
        """
        try:
            if budget < 0:
                error = ValidationError("Budget cannot be negative", field="budget", value=budget)
                return False, error_handler.handle_error(error)
                
            min_budget, max_budget = self.historical_data_client.get_budget_range()
            
            if budget < min_budget:
                error = ValidationError(
                    f"Budget of ${budget} is too low. Effective campaigns typically use ${min_budget}-${max_budget}",
                    field="budget",
                    value=budget
                )
                return False, error_handler.handle_error(error)
                
            if budget > max_budget * 2: # Allow some leeway
                error = ValidationError(
                    f"Budget of ${budget} is unusually high. Typical range is ${min_budget}-${max_budget}",
                    field="budget", 
                    value=budget
                )
                return False, error_handler.handle_error(error)
                
            return True, ""
        except Exception as e:
            error_message = error_handler.handle_error(e, context={"operation": "budget validation", "budget": budget})
            return False, error_message

    def validate_cpa(self, cpa: float) -> tuple[bool, str]:
        """
        Validates the target CPA against historical data.
        Returns (is_valid, feedback_message).
        """
        try:
            if cpa < 0:
                error = ValidationError("CPA cannot be negative", field="cpa", value=cpa)
                return False, error_handler.handle_error(error)
                
            min_cpa, max_cpa = self.historical_data_client.get_cpa_range()
            
            if cpa < min_cpa:
                error = ValidationError(
                    f"CPA of ${cpa} might be too low to be competitive. Typical range: ${min_cpa}-${max_cpa}",
                    field="cpa",
                    value=cpa
                )
                return False, error_handler.handle_error(error)
                
            if cpa > max_cpa:
                error = ValidationError(
                    f"CPA of ${cpa} is high and might result in overpaying. Typical range: ${min_cpa}-${max_cpa}",
                    field="cpa",
                    value=cpa
                )
                return False, error_handler.handle_error(error)
                
            return True, ""
        except Exception as e:
            error_message = error_handler.handle_error(e, context={"operation": "CPA validation", "cpa": cpa})
            return False, error_message

    def validate_platform(self, platform: str) -> tuple[bool, str]:
        """
        Validates the target platform.
        Returns (is_valid, feedback_message).
        """
        try:
            if not platform or not platform.strip():
                error = ValidationError("Platform cannot be empty", field="platform", value=platform)
                return False, error_handler.handle_error(error)
                
            valid_platforms = ["Desktop", "Mobile", "Both"]
            if platform not in valid_platforms:
                error = ValidationError(
                    f"Platform '{platform}' is not supported. Valid options: Desktop, Mobile, or Both",
                    field="platform",
                    value=platform
                )
                return False, error_handler.handle_error(error)
                
            return True, ""
        except Exception as e:
            error_message = error_handler.handle_error(e, context={"operation": "platform validation", "platform": platform})
            return False, error_message
