from abc import ABC, abstractmethod
import logging
import traceback
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from .error_types import (
    CampaignAssistantError, ErrorCategory, ErrorSeverity,
    ValidationError, ApiError, ConversationError,
    DataProcessingError, MigrationError, OptimizationError, SystemError
)


class ErrorHandler(ABC):
    """
    Abstract base class for Error Handlers.
    """

    @abstractmethod
    def handle_error(self, error: Exception) -> str:
        """
        Handles an error and returns an error message.

        Args:
            error: The error to handle.

        Returns:
            An error message.
        """
        pass


class CampaignAssistantErrorHandler:
    """
    Comprehensive error handler for the campaign assistant system.
    Manages invalid inputs, API errors, and provides appropriate error messages.
    """

    def __init__(self):
        # Set up dedicated error logger
        self.error_logger = logging.getLogger('campaign_assistant.errors')
        self.error_logger.setLevel(logging.ERROR)
        
        # Create error log file handler if not exists
        if not self.error_logger.handlers:
            error_file_handler = logging.FileHandler('campaign_assistant_errors.log')
            error_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            error_file_handler.setFormatter(error_formatter)
            self.error_logger.addHandler(error_file_handler)
            
        # Error statistics
        self.error_stats: Dict[str, int] = {}
        
    def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Central error handling method that categorizes, logs, and formats errors.
        
        Args:
            error: The error to handle
            context: Additional context information
            
        Returns:
            User-friendly error message
        """
        # Convert standard exceptions to CampaignAssistantError if needed
        if not isinstance(error, CampaignAssistantError):
            error = self._convert_to_campaign_error(error, context)
            
        # Log the error
        self._log_error(error, context)
        
        # Update error statistics
        self._update_error_stats(error)
        
        # Generate user-friendly message
        user_message = self._generate_user_message(error)
        
        return user_message
    
    def _convert_to_campaign_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> CampaignAssistantError:
        """Convert standard exceptions to CampaignAssistantError."""
        error_message = str(error)
        
        # Categorize based on error type or message content
        if isinstance(error, ValueError):
            return ValidationError(error_message, context=context, original_error=error)
        elif isinstance(error, ConnectionError) or 'API' in error_message or 'HTTP' in error_message:
            return ApiError(error_message, context=context, original_error=error)
        elif isinstance(error, KeyError) or isinstance(error, AttributeError):
            return DataProcessingError(error_message, context=context, original_error=error)
        else:
            return SystemError(error_message, context=context, original_error=error)
    
    def _log_error(self, error: CampaignAssistantError, context: Optional[Dict[str, Any]] = None):
        """Log error details comprehensively."""
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'category': error.category.value,
            'severity': error.severity.value,
            'message': error.message,
            'context': {**error.context, **(context or {})},
            'traceback': traceback.format_exc() if error.original_error else None
        }
        
        log_message = f"[{error.category.value.upper()}] {error.message}"
        if error.context:
            log_message += f" | Context: {json.dumps(error.context, default=str)}"
            
        if error.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            self.error_logger.critical(log_message)
        elif error.severity == ErrorSeverity.MEDIUM:
            self.error_logger.error(log_message)
        else:
            self.error_logger.warning(log_message)
    
    def _update_error_stats(self, error: CampaignAssistantError):
        """Track error statistics for monitoring."""
        category_key = error.category.value
        severity_key = f"{error.category.value}_{error.severity.value}"
        
        self.error_stats[category_key] = self.error_stats.get(category_key, 0) + 1
        self.error_stats[severity_key] = self.error_stats.get(severity_key, 0) + 1
        self.error_stats['total'] = self.error_stats.get('total', 0) + 1
    
    def _generate_user_message(self, error: CampaignAssistantError) -> str:
        """Generate user-friendly error messages based on error category."""
        
        if error.category == ErrorCategory.VALIDATION:
            return self._generate_validation_message(error)
        elif error.category == ErrorCategory.API:
            return self._generate_api_message(error)
        elif error.category == ErrorCategory.CONVERSATION:
            return self._generate_conversation_message(error)
        elif error.category == ErrorCategory.DATA_PROCESSING:
            return self._generate_data_processing_message(error)
        elif error.category == ErrorCategory.MIGRATION:
            return self._generate_migration_message(error)
        elif error.category == ErrorCategory.OPTIMIZATION:
            return self._generate_optimization_message(error)
        else:
            return self._generate_system_message(error)
    
    def _generate_validation_message(self, error: ValidationError) -> str:
        """Generate user-friendly validation error messages."""
        field = error.context.get('field')
        if field:
            return f"The {field} you provided is not valid. {error.message}"
        return f"Input validation failed: {error.message}"
    
    def _generate_api_message(self, error: ApiError) -> str:
        """Generate user-friendly API error messages."""
        api_name = error.context.get('api_name', 'external service')
        if 'timeout' in error.message.lower():
            return f"The {api_name} is taking longer than usual to respond. Please try again in a moment."
        elif 'connection' in error.message.lower():
            return f"Unable to connect to {api_name}. Please check your internet connection and try again."
        else:
            return f"There's an issue with the {api_name}. Our team has been notified. Please try again later."
    
    def _generate_conversation_message(self, error: ConversationError) -> str:
        """Generate user-friendly conversation error messages."""
        return f"I'm having trouble understanding the current conversation context. {error.message} Let's try again."
    
    def _generate_data_processing_message(self, error: DataProcessingError) -> str:
        """Generate user-friendly data processing error messages."""
        operation = error.context.get('operation', 'processing your request')
        return f"I encountered an issue while {operation}. Please verify your input and try again."
    
    def _generate_migration_message(self, error: MigrationError) -> str:
        """Generate user-friendly migration error messages."""
        platform = error.context.get('source_platform', 'the source platform')
        return f"There was an issue migrating your campaign from {platform}. {error.message}"
    
    def _generate_optimization_message(self, error: OptimizationError) -> str:
        """Generate user-friendly optimization error messages."""
        return f"I couldn't generate optimization suggestions at the moment. {error.message} Please try again."
    
    def _generate_system_message(self, error: SystemError) -> str:
        """Generate user-friendly system error messages."""
        if error.severity == ErrorSeverity.CRITICAL:
            return "I'm experiencing technical difficulties. Please contact support for assistance."
        else:
            return "Something unexpected happened. Please try again, and if the issue persists, contact support."
    
    def get_error_stats(self) -> Dict[str, int]:
        """Return current error statistics."""
        return self.error_stats.copy()
    
    def reset_error_stats(self):
        """Reset error statistics."""
        self.error_stats.clear()
    
    def create_validation_error(self, message: str, field: str = None, value: Any = None) -> ValidationError:
        """Helper method to create validation errors."""
        return ValidationError(message, field=field, value=value)
    
    def create_api_error(self, message: str, api_name: str = None, status_code: int = None) -> ApiError:
        """Helper method to create API errors."""
        return ApiError(message, api_name=api_name, status_code=status_code)
    
    def create_conversation_error(self, message: str, state: str = None) -> ConversationError:
        """Helper method to create conversation errors."""
        return ConversationError(message, state=state)


# Global error handler instance
error_handler = CampaignAssistantErrorHandler()
