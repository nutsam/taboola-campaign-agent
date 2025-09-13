#!/usr/bin/env python3

import logging
import os
from core.error_handler import (
    error_handler, ValidationError, ApiError, ConversationError,
    DataProcessingError, MigrationError, OptimizationError, SystemError,
    ErrorCategory, ErrorSeverity
)
from core.error_handler.error_recovery import error_recovery_manager, with_retry, with_fallback
from core.data_processor.data_processor import DataProcessor
from core.conversation_manager.conversation_manager import ConversationManager
from external.api_clients import TaboolaHistoricalDataClient, TaboolaApiClient, FacebookApiClient
from core.optimization_suggestion_engine.optimization_suggestion_engine import OptimizationSuggestionEngine
from core.migration_module.migration_module import MigrationModule
from response_generator.response_generator import ResponseGenerator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_error_types():
    """Test different error types and their handling."""
    print("=== Testing Error Types ===\n")
    
    # Test validation errors
    validation_error = ValidationError("Invalid budget", field="budget", value=-100)
    message = error_handler.handle_error(validation_error)
    print(f"Validation Error: {message}")
    
    # Test API errors
    api_error = ApiError("Connection timeout", api_name="OpenAI", status_code=504)
    message = error_handler.handle_error(api_error)
    print(f"API Error: {message}")
    
    # Test conversation errors
    conversation_error = ConversationError("Invalid state", state="optimization")
    message = error_handler.handle_error(conversation_error)
    print(f"Conversation Error: {message}")
    
    # Test standard exception conversion
    standard_error = ValueError("Invalid input format")
    message = error_handler.handle_error(standard_error)
    print(f"Standard Error (converted): {message}")
    
    print(f"\nError Statistics: {error_handler.get_error_stats()}")

def test_data_processor_error_handling():
    """Test error handling in DataProcessor."""
    print("\n=== Testing DataProcessor Error Handling ===\n")
    
    try:
        historical_client = TaboolaHistoricalDataClient()
        data_processor = DataProcessor(historical_client)
        
        # Test various invalid inputs
        test_cases = [
            ("validate_url", [""]),  # Empty URL
            ("validate_url", ["invalid-url"]),  # URL without protocol
            ("validate_budget", [-50]),  # Negative budget
            ("validate_cpa", [-10]),  # Negative CPA
            ("validate_platform", [""]),  # Empty platform
            ("validate_platform", ["Invalid"]),  # Invalid platform
        ]
        
        for method_name, args in test_cases:
            method = getattr(data_processor, method_name)
            is_valid, message = method(*args)
            print(f"{method_name}{args}: Valid={is_valid}, Message='{message}'")
            
    except Exception as e:
        print(f"DataProcessor test failed: {e}")

def test_error_recovery():
    """Test error recovery mechanisms."""
    print("\n=== Testing Error Recovery ===\n")
    
    # Test validation error recovery
    validation_error = ValidationError("Budget too low", field="budget", value=10)
    recovery = error_recovery_manager.attempt_recovery(validation_error)
    print(f"Validation Error Recovery: {recovery}")
    
    # Test API error recovery
    api_error = ApiError("Timeout occurred", api_name="OpenAI")
    recovery = error_recovery_manager.attempt_recovery(api_error)
    print(f"API Error Recovery: {recovery}")
    
    # Test conversation error recovery
    conversation_error = ConversationError("Lost state")
    recovery = error_recovery_manager.attempt_recovery(conversation_error)
    print(f"Conversation Error Recovery: {recovery}")

@with_retry()
def flaky_function(fail_count=2):
    """Simulates a function that fails the first few times."""
    if not hasattr(flaky_function, 'attempt_count'):
        flaky_function.attempt_count = 0
    
    flaky_function.attempt_count += 1
    
    if flaky_function.attempt_count <= fail_count:
        raise ConnectionError(f"Simulated failure {flaky_function.attempt_count}")
    
    return f"Success on attempt {flaky_function.attempt_count}"

def fallback_function(*args, **kwargs):
    """Fallback function for testing."""
    return "Fallback result"

@with_fallback(fallback_function)
def main_function():
    """Main function that always fails for testing."""
    raise RuntimeError("Main function always fails")

def test_retry_and_fallback():
    """Test retry and fallback decorators."""
    print("\n=== Testing Retry and Fallback Mechanisms ===\n")
    
    # Test retry decorator
    try:
        flaky_function.attempt_count = 0  # Reset counter
        result = flaky_function(fail_count=2)
        print(f"Retry test result: {result}")
    except Exception as e:
        print(f"Retry test failed: {e}")
    
    # Test fallback decorator
    try:
        result = main_function()
        print(f"Fallback test result: {result}")
    except Exception as e:
        print(f"Fallback test failed: {e}")

def test_conversation_error_handling():
    """Test error handling in conversation flow."""
    print("\n=== Testing Conversation Error Handling ===\n")
    
    try:
        # Initialize components
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
        
        # Test error scenarios
        error_scenarios = [
            "",  # Empty message
            None,  # None message (will be converted to string)
        ]
        
        for scenario in error_scenarios:
            if scenario is not None:
                print(f"Testing scenario: '{scenario}'")
                try:
                    result = conversation_manager.handle_message(scenario)
                    print(f"Result: {result}")
                except Exception as e:
                    print(f"Exception: {e}")
            
    except Exception as e:
        print(f"Conversation error handling test failed: {e}")

def test_error_logging():
    """Test error logging functionality."""
    print("\n=== Testing Error Logging ===\n")
    
    # Check if log file will be created
    log_file = "campaign_assistant_errors.log"
    initial_size = 0
    if os.path.exists(log_file):
        initial_size = os.path.getsize(log_file)
        
    # Generate some errors to log
    errors = [
        ValidationError("Test validation error", field="test", severity=ErrorSeverity.LOW),
        ApiError("Test API error", api_name="TestAPI", severity=ErrorSeverity.MEDIUM),
        SystemError("Test system error", component="TestComponent", severity=ErrorSeverity.HIGH)
    ]
    
    for error in errors:
        error_handler.handle_error(error)
    
    # Check if log file grew
    if os.path.exists(log_file):
        final_size = os.path.getsize(log_file)
        print(f"Log file size increased: {final_size - initial_size} bytes")
        
        # Read last few lines
        with open(log_file, 'r') as f:
            lines = f.readlines()
            if lines:
                print("Last log entry:")
                print(lines[-1].strip())
    else:
        print("Log file was not created")

def main():
    """Run all error handling tests."""
    print("🛠️  Error Handling System Tests")
    print("=" * 50)
    
    try:
        test_error_types()
        test_data_processor_error_handling()
        test_error_recovery()
        test_retry_and_fallback()
        test_conversation_error_handling()
        test_error_logging()
        
        print("\n" + "=" * 50)
        print("✅ All error handling tests completed!")
        print(f"📊 Final Error Statistics: {error_handler.get_error_stats()}")
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()