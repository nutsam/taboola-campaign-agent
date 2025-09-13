"""
Error types and custom exceptions for the campaign assistant system.
"""

from enum import Enum
from typing import Optional, Dict, Any


class ErrorCategory(Enum):
    """Categories of errors that can occur in the system."""
    VALIDATION = "validation"
    API = "api"
    CONVERSATION = "conversation"
    DATA_PROCESSING = "data_processing"
    MIGRATION = "migration"
    OPTIMIZATION = "optimization"
    SYSTEM = "system"


class ErrorSeverity(Enum):
    """Severity levels for errors."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CampaignAssistantError(Exception):
    """Base exception class for campaign assistant errors."""
    
    def __init__(
        self, 
        message: str, 
        category: ErrorCategory,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.category = category
        self.severity = severity
        self.context = context or {}
        self.original_error = original_error


class ValidationError(CampaignAssistantError):
    """Error for invalid user inputs or data validation failures."""
    
    def __init__(self, message: str, field: str = None, value: Any = None, **kwargs):
        context = kwargs.get('context', {})
        if field:
            context['field'] = field
        if value is not None:
            context['value'] = value
        kwargs['context'] = context
        super().__init__(message, ErrorCategory.VALIDATION, **kwargs)


class ApiError(CampaignAssistantError):
    """Error for API-related failures."""
    
    def __init__(self, message: str, api_name: str = None, status_code: int = None, **kwargs):
        context = kwargs.get('context', {})
        if api_name:
            context['api_name'] = api_name
        if status_code:
            context['status_code'] = status_code
        kwargs['context'] = context
        super().__init__(message, ErrorCategory.API, **kwargs)


class ConversationError(CampaignAssistantError):
    """Error for conversation flow issues."""
    
    def __init__(self, message: str, state: str = None, **kwargs):
        context = kwargs.get('context', {})
        if state:
            context['conversation_state'] = state
        kwargs['context'] = context
        super().__init__(message, ErrorCategory.CONVERSATION, **kwargs)


class DataProcessingError(CampaignAssistantError):
    """Error for data processing failures."""
    
    def __init__(self, message: str, operation: str = None, **kwargs):
        context = kwargs.get('context', {})
        if operation:
            context['operation'] = operation
        kwargs['context'] = context
        super().__init__(message, ErrorCategory.DATA_PROCESSING, **kwargs)


class MigrationError(CampaignAssistantError):
    """Error for campaign migration failures."""
    
    def __init__(self, message: str, source_platform: str = None, campaign_id: str = None, **kwargs):
        context = kwargs.get('context', {})
        if source_platform:
            context['source_platform'] = source_platform
        if campaign_id:
            context['campaign_id'] = campaign_id
        kwargs['context'] = context
        super().__init__(message, ErrorCategory.MIGRATION, **kwargs)


class OptimizationError(CampaignAssistantError):
    """Error for optimization suggestion failures."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, ErrorCategory.OPTIMIZATION, **kwargs)


class SystemError(CampaignAssistantError):
    """Error for system-level failures."""
    
    def __init__(self, message: str, component: str = None, **kwargs):
        context = kwargs.get('context', {})
        if component:
            context['component'] = component
        kwargs['context'] = context
        kwargs['severity'] = kwargs.get('severity', ErrorSeverity.HIGH)
        super().__init__(message, ErrorCategory.SYSTEM, **kwargs)