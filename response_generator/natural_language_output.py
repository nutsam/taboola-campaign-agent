from abc import ABC, abstractmethod

class ResponseGenerator(ABC):
    """
    Abstract base class for Response Generators.
    """

    @abstractmethod
    def generate_response(self, data: dict) -> str:
        """
        Generates a natural language response.

        Args:
            data: The data to generate the response from.

        Returns:
            The natural language response.
        """
        pass
