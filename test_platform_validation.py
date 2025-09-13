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

def test_platform_validation():
    """Test platform validation specifically"""
    print("=== Testing Platform Validation ===\n")
    
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

        # Test platform validation directly
        print("Direct platform validation tests:")
        test_platforms = ["Desktop", "Mobile", "Both", "All", "Invalid", "desktop", ""]
        
        for platform in test_platforms:
            is_valid, message = data_processor.validate_platform(platform)
            print(f"  Platform '{platform}' -> Valid: {is_valid}, Message: '{message}'")
        
        print("\n" + "="*50 + "\n")
        
        # Test in conversation context
        conversation_manager = ConversationManager(
            suggestion_engine=suggestion_engine,
            migration_module=migration_module,
            data_processor=data_processor,
            response_generator=response_generator,
            task='optimization'
        )
        
        # Set up conversation to CPA validated state by simulating the full flow
        print("Setting up conversation state...")
        conversation_manager.handle_message("Hello")
        conversation_manager.handle_message("create campaign")
        conversation_manager.handle_message("http://www.google.com")
        conversation_manager.handle_message("100")
        conversation_manager.handle_message("5")
        print("Conversation is now ready for platform input.\n")
        
        # Simulate platform input messages
        platform_inputs = ["All", "Desktop", "Invalid", "mobile"]
        
        for platform_input in platform_inputs:
            print(f"Testing platform input: '{platform_input}'")
            try:
                response = conversation_manager.handle_message(platform_input)
                print(f"AI Response: {response}\n")
            except Exception as e:
                print(f"Error: {e}\n")
                
        print("=== Platform Validation Test Completed ===")
        
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    test_platform_validation()