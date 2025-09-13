from abc import ABC, abstractmethod

class NlpParser(ABC):
    """
    Abstract base class for NLP Parsers.
    """

    @abstractmethod
    def parse_input(self, user_message: str) -> dict:
        """
        Parses the user's message and extracts relevant information.

        Args:
            user_message: The raw input string from the user.

        Returns:
            A dictionary containing the parsed input.
        """
        pass
