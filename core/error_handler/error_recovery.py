"""
Error recovery mechanisms for the campaign assistant system.
Provides automatic retry logic and graceful degradation.
"""

import time
import logging
from typing import Callable, Any, Dict, Optional, List
from functools import wraps
from .error_types import CampaignAssistantError, ErrorCategory, ErrorSeverity, ApiError, SystemError
from .error_handler import error_handler


class RetryConfig:
    """Configuration for retry behavior."""
    
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter


class ErrorRecoveryManager:
    """Manages error recovery strategies for different error types."""
    
    def __init__(self):
        self.recovery_strategies: Dict[ErrorCategory, Callable] = {
            ErrorCategory.API: self._recover_api_error,
            ErrorCategory.VALIDATION: self._recover_validation_error,
            ErrorCategory.CONVERSATION: self._recover_conversation_error,
            ErrorCategory.DATA_PROCESSING: self._recover_data_processing_error,
            ErrorCategory.MIGRATION: self._recover_migration_error,
            ErrorCategory.OPTIMIZATION: self._recover_optimization_error,
            ErrorCategory.SYSTEM: self._recover_system_error
        }
        
        # Default retry configurations for different error types
        self.retry_configs = {
            ErrorCategory.API: RetryConfig(max_attempts=3, base_delay=2.0),
            ErrorCategory.DATA_PROCESSING: RetryConfig(max_attempts=2, base_delay=1.0),
            ErrorCategory.SYSTEM: RetryConfig(max_attempts=1, base_delay=5.0)
        }
    
    def attempt_recovery(self, error: CampaignAssistantError, context: Dict[str, Any] = None) -> Optional[Any]:
        """
        Attempt to recover from an error using appropriate strategy.
        
        Args:
            error: The error to recover from
            context: Additional context for recovery
            
        Returns:
            Recovery result if successful, None otherwise
        """
        try:
            recovery_func = self.recovery_strategies.get(error.category)
            if recovery_func:
                return recovery_func(error, context or {})
        except Exception as recovery_error:
            # Log recovery failure
            error_handler.handle_error(recovery_error, context={
                "operation": "error_recovery",
                "original_error": str(error),
                "error_category": error.category.value
            })
        return None
    
    def _recover_api_error(self, error: ApiError, context: Dict[str, Any]) -> Optional[Any]:
        """Recovery strategy for API errors."""
        api_name = error.context.get('api_name', 'unknown')
        
        if 'timeout' in error.message.lower():
            return {"suggestion": "retry_with_longer_timeout", "delay": 5.0}
        elif 'rate limit' in error.message.lower():
            return {"suggestion": "retry_with_backoff", "delay": 30.0}
        elif 'connection' in error.message.lower():
            return {"suggestion": "check_connectivity", "delay": 10.0}
        
        return {"suggestion": "use_fallback_api", "api_name": api_name}
    
    def _recover_validation_error(self, error: CampaignAssistantError, context: Dict[str, Any]) -> Optional[Any]:
        """Recovery strategy for validation errors."""
        field = error.context.get('field')
        value = error.context.get('value')
        
        suggestions = []
        
        if field == 'budget' and isinstance(value, (int, float)):
            if value < 0:
                suggestions.append("Set budget to minimum value: $50")
            elif value < 50:
                suggestions.append("Increase budget to at least $50")
        elif field == 'cpa' and isinstance(value, (int, float)):
            if value < 0:
                suggestions.append("Set CPA to minimum value: $2")
            elif value < 2:
                suggestions.append("Increase CPA to at least $2")
        elif field == 'url' and isinstance(value, str):
            if not value.startswith(('http://', 'https://')):
                suggestions.append(f"Add protocol: https://{value}")
        elif field == 'platform' and isinstance(value, str):
            if value.lower() in ['desktop', 'mobile', 'both']:
                suggestions.append(f"Use correct case: {value.capitalize()}")
            elif 'all' in value.lower():
                suggestions.append("Use 'Both' instead of 'All'")
        
        return {"suggestions": suggestions} if suggestions else None
    
    def _recover_conversation_error(self, error: CampaignAssistantError, context: Dict[str, Any]) -> Optional[Any]:
        """Recovery strategy for conversation errors."""
        return {
            "suggestion": "reset_conversation_state",
            "message": "Let's start fresh. What would you like to do?"
        }
    
    def _recover_data_processing_error(self, error: CampaignAssistantError, context: Dict[str, Any]) -> Optional[Any]:
        """Recovery strategy for data processing errors."""
        operation = error.context.get('operation')
        
        if operation in ['budget_validation', 'cpa_validation', 'url_validation', 'platform_validation']:
            return {
                "suggestion": "request_input_again",
                "message": f"There was an issue with your {operation.split('_')[0]}. Please try entering it again."
            }
        
        return {"suggestion": "use_default_values"}
    
    def _recover_migration_error(self, error: CampaignAssistantError, context: Dict[str, Any]) -> Optional[Any]:
        """Recovery strategy for migration errors."""
        source_platform = error.context.get('source_platform')
        
        return {
            "suggestion": "retry_migration",
            "message": f"Migration from {source_platform} failed. Would you like to try again or use manual input?"
        }
    
    def _recover_optimization_error(self, error: CampaignAssistantError, context: Dict[str, Any]) -> Optional[Any]:
        """Recovery strategy for optimization errors."""
        return {
            "suggestion": "use_basic_suggestions",
            "message": "I couldn't generate advanced suggestions, but I can provide basic recommendations."
        }
    
    def _recover_system_error(self, error: CampaignAssistantError, context: Dict[str, Any]) -> Optional[Any]:
        """Recovery strategy for system errors."""
        if error.severity == ErrorSeverity.CRITICAL:
            return {
                "suggestion": "graceful_shutdown",
                "message": "System needs to restart. Please try again later."
            }
        else:
            return {
                "suggestion": "continue_with_limitations",
                "message": "Some features may be limited. Basic functionality is available."
            }


def with_retry(retry_config: RetryConfig = None):
    """
    Decorator to add retry logic to functions.
    
    Args:
        retry_config: Configuration for retry behavior
    """
    if retry_config is None:
        retry_config = RetryConfig()
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(retry_config.max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    # Don't retry on certain error types
                    if isinstance(e, CampaignAssistantError) and e.category == ErrorCategory.VALIDATION:
                        raise e
                    
                    if attempt < retry_config.max_attempts - 1:
                        delay = min(
                            retry_config.base_delay * (retry_config.exponential_base ** attempt),
                            retry_config.max_delay
                        )
                        
                        if retry_config.jitter:
                            import random
                            delay *= (0.5 + random.random() * 0.5)
                        
                        logging.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.2f}s...")
                        time.sleep(delay)
                    else:
                        logging.error(f"All {retry_config.max_attempts} attempts failed. Last error: {e}")
            
            # If we get here, all retries failed
            raise last_exception
        
        return wrapper
    return decorator


def with_fallback(fallback_func: Callable):
    """
    Decorator to provide fallback functionality when main function fails.
    
    Args:
        fallback_func: Function to call if main function fails
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logging.warning(f"Main function {func.__name__} failed: {e}. Using fallback.")
                try:
                    return fallback_func(*args, **kwargs)
                except Exception as fallback_error:
                    logging.error(f"Fallback also failed: {fallback_error}")
                    raise e  # Raise original error
        
        return wrapper
    return decorator


# Global error recovery manager
error_recovery_manager = ErrorRecoveryManager()