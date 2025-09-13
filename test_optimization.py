#!/usr/bin/env python3

import logging
from core.optimization_suggestion_engine.optimization_suggestion_engine import OptimizationSuggestionEngine
from core.conversation_manager.conversation_manager import ConversationManager
from core.migration_module.migration_module import MigrationModule
from core.data_processor.data_processor import DataProcessor
from external.api_clients import (
    TaboolaHistoricalDataClient,
    FacebookApiClient,
    TaboolaApiClient
)
from response_generator.response_generator import ResponseGenerator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_optimization_flow():
    """Test the optimization conversation flow"""
    print("=== Testing Optimization Flow ===\n")
    
    # Initialize components
    try:
        historical_data_client = TaboolaHistoricalDataClient()
        taboola_client = TaboolaApiClient()
        facebook_client = FacebookApiClient()
        source_clients = {'facebook': facebook_client}
        suggestion_engine = OptimizationSuggestionEngine(historical_data_client=historical_data_client)
        migration_module = MigrationModule(taboola_client=taboola_client, source_clients=source_clients)
        data_processor = DataProcessor(historical_data_client=historical_data_client)
        response_generator = ResponseGenerator()

        conversation_manager = ConversationManager(
            suggestion_engine=suggestion_engine,
            migration_module=migration_module,
            data_processor=data_processor,
            response_generator=response_generator,
            task='optimization'
        )
        
        print("✓ All components initialized successfully\n")
        
        # Test conversation flow
        messages = [
            "Hello",
            "create campaign", 
            "www.google.com",
            "http://www.google.com",
            "0",     # Invalid budget
            "100",   # Valid budget
            "5",     # Valid CPA
            "Invalid", # Invalid platform
            "Desktop" # Valid platform
        ]
        
        for i, message in enumerate(messages):
            print(f"User: {message}")
            try:
                response = conversation_manager.handle_message(message)
                print(f"AI: {response}\n")
            except Exception as e:
                print(f"Error processing message '{message}': {e}\n")
                
        print("=== Test Completed ===")
        
    except Exception as e:
        print(f"Initialization failed: {e}")

if __name__ == "__main__":
    test_optimization_flow()