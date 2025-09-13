from abc import ABC, abstractmethod

class SessionStorage(ABC):
    """
    Abstract base class for Session Storage.
    """

    @abstractmethod
    def store_data(self, session_id: str, data: dict):
        """
        Stores session data.

        Args:
            session_id: The ID of the session.
            data: The data to store.
        """
        pass

    @abstractmethod
    def get_data(self, session_id: str) -> dict:
        """
        Retrieves session data.

        Args:
            session_id: The ID of the session.

        Returns:
            The session data.
        """
        pass
