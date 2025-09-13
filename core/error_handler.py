from abc import ABC, abstractmethod

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
