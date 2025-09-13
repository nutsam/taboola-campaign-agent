import logging
from external.api_clients import TaboolaHistoricalDataClient

class OptimizationSuggestionEngine:
    """Analyzes input data against Taboola's historical campaign data to generate suggestions."""

    def __init__(self, historical_data_client: TaboolaHistoricalDataClient):
        """
        Initializes the engine with a client to Taboola's historical campaign data warehouse.
        """
        self.historical_data_client = historical_data_client
        logging.info("OptimizationSuggestionEngine initialized with TaboolaHistoricalDataClient.")

    def get_suggestions(self, user_campaign_data: dict) -> list[str]:
        """Main method to generate campaign suggestions."""
        logging.info("\n--- Starting Suggestion Generation using Taboola's Data ---")
        logging.info(f"1. Analyzing user's campaign data: {user_campaign_data}")

        logging.info("2. Finding similar successful Taboola campaigns via API client...")
        similar_campaigns = self._find_similar_campaigns(user_campaign_data)

        if not similar_campaigns:
            return ["Could not find enough similar campaigns on Taboola to generate suggestions."]
        logging.info(f"   Found {len(similar_campaigns)} similar campaigns.")

        # In a real system, success would be determined by more than just ROI
        successful_campaigns = [c for c in similar_campaigns if c.get('roi', 0) > 1.0]
        if not successful_campaigns:
            return ["Found similar campaigns, but none met the success criteria for generating reliable suggestions."]
        logging.info(f"   Identified {len(successful_campaigns)} successful campaigns to learn from.")

        logging.info("4. Learning patterns from successful Taboola campaigns...")
        learned_patterns = self._extract_patterns(successful_campaigns)
        logging.info(f"   Learned patterns: {learned_patterns}")

        logging.info("5. Generating personalized suggestions...")
        suggestions = self._generate_suggestions(learned_patterns, user_campaign_data)
        logging.info("--- Suggestion Generation Complete ---")

        return suggestions

    def _find_similar_campaigns(self, user_campaign_data: dict) -> list[dict]:
        """Fetches similar campaigns using the injected Taboola historical data client."""
        return self.historical_data_client.get_similar_campaigns(user_campaign_data)

    def _extract_patterns(self, successful_campaigns: list[dict]) -> dict:
        """Analyzes a set of successful campaigns to find common, high-performing attributes."""
        logging.info("   - Analyzing commonalities in CPC, targeting, etc., from successful campaigns.")
        
        # Example: Find the average CPC bid from successful campaigns
        total_cpc = sum(c.get('cpc_bid', 0.5) for c in successful_campaigns)
        avg_cpc = total_cpc / len(successful_campaigns) if successful_campaigns else 0.5

        return {
            'avg_cpc_bid': round(avg_cpc, 2),
        }

    def _generate_suggestions(self, learned_patterns: dict, user_campaign_data: dict) -> list[str]:
        """Generates human-readable suggestions based on learned patterns from Taboola data."""
        suggestions = []
        
        # Suggest a CPC bid based on successful campaigns
        avg_cpc = learned_patterns['avg_cpc_bid']
        suggestion = f"Consider a starting CPC bid around ${avg_cpc}. This is a competitive bid based on similar successful campaigns on Taboola."
        suggestions.append(suggestion)

        return suggestions