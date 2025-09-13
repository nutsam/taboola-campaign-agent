from abc import ABC, abstractmethod

class DataProcessor(ABC):
    """
    Abstract base class for Data Processors.
    """

    @abstractmethod
    def validate_and_store_inputs(self, inputs: dict) -> bool:
        """
        Validates and stores user inputs.

        Args:
            inputs: The parsed inputs from the user.

        Returns:
            True if the inputs are valid, False otherwise.
        """
        pass
