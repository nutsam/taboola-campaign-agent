from abc import ABC, abstractmethod

class UserInterface(ABC):
    """
    Abstract base class for User Interfaces.
    """

    @abstractmethod
    def get_user_input(self) -> str:
        """
        Gets input from the user.

        Returns:
            The user's input.
        """
        pass

    @abstractmethod
    def display_response(self, response: str):
        """
        Displays a response to the user.

        Args:
            response: The response to display.
        """
        pass
