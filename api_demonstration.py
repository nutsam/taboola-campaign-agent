import logging
import json

# Core logic imports
from core.optimization_suggestion_engine import OptimizationSuggestionEngine
from core.conversation_manager import ConversationManager
from core.migration_module import MigrationModule

# API client imports
from external.api_clients import (
    NlpApiClient,
    TaboolaHistoricalDataClient, # Updated client name
    FacebookApiClient,
    TaboolaApiClient
)

def run_demonstration():
    """
    Runs a demonstration of the updated, Taboola-centric application logic.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - DEMO - %(levelname)s - %(message)s')

    # --- Setup: Initialize all modules and clients ---
    logging.info("--- Initializing application components with Taboola-centric mocks ---")
    nlp_client = NlpApiClient()
    historical_data_client = TaboolaHistoricalDataClient() # Updated client
    taboola_client = TaboolaApiClient()
    facebook_client = FacebookApiClient()
    source_clients = {'facebook': facebook_client}

    suggestion_engine = OptimizationSuggestionEngine(historical_data_client=historical_data_client)
    conversation_manager = ConversationManager(suggestion_engine=suggestion_engine, nlp_client=nlp_client)
    migration_module = MigrationModule(taboola_client=taboola_client, source_clients=source_clients)
    logging.info("--- Initialization Complete")


    # --- 1. Demonstrate the Chat Logic with new Taboola-based suggestions ---
    logging.info("\n--- Demonstrating Chat Logic ---")
    user_messages = [
        "Hi, I need help with a new campaign.",
        "My campaign url is http://my-new-tech-product.com",
        "My daily budget is $100",
        "My target CPA is $15",
        "We want to target all platforms."
    ]
    for msg in user_messages:
        ai_response = conversation_manager.handle_message(msg)
    logging.info(f"\nFinal AI response from conversation:\n{ai_response}")


    # --- 2. Demonstrate the Migration Logic with Success and Failure cases ---
    logging.info("\n\n--- Demonstrating Migration Logic ---")
    
    # Case 1: Successful Migration
    logging.info("\n--- Case 1: Successful Migration ---")
    report_success = migration_module.migrate_campaign(
        source_platform="facebook",
        campaign_id="fb_campaign_12345"
    )

    # Case 2: Failed Migration (due to missing data)
    logging.info("\n--- Case 2: Failed Migration (API Validation Error) ---")
    # We'll simulate a mapping that omits required fields for the Taboola API.
    # The `data_override` will unset a required field.
    report_failure = migration_module.migrate_campaign(
        source_platform="facebook",
        campaign_id="fb_campaign_12345",
        data_override={'cpc_bid': None} # This will cause our mock API to fail
    )

if __name__ == "__main__":
    run_demonstration()
