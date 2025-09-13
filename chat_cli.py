import logging
from core.optimization_suggestion_engine.optimization_suggestion_engine import OptimizationSuggestionEngine
from core.conversation_manager.conversation_manager import ConversationManager
from core.migration_module.migration_module import MigrationModule
from external.api_clients import (
    TaboolaHistoricalDataClient,
    FacebookApiClient,
    TaboolaApiClient
)
from user_interface.chat_input import UserInterface

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class CliInterface(UserInterface):
    """
    A command-line interface for interacting with the AI agent.
    """
    def get_user_input(self) -> str:
        """Gets input from the user via the command line."""
        return input("You: ")

    def display_response(self, response: str):
        """Displays a response to the user in the command line."""
        print(f"AI: {response}")

def main():
    """
    Main function to run the CLI chat application.
    """
    print("Initializing AI Campaign Assistant...")
    
    # 1. Initialize API Clients and Core Modules
    try:
        historical_data_client = TaboolaHistoricalDataClient()
        taboola_client = TaboolaApiClient()
        facebook_client = FacebookApiClient()
        source_clients = {'facebook': facebook_client}        
        suggestion_engine = OptimizationSuggestionEngine(historical_data_client=historical_data_client)
        migration_module = MigrationModule(taboola_client=taboola_client, source_clients=source_clients)
        
        # Ask user for the task
        task = ""
        while task not in ["optimization", "migration"]:
            task = input("What task would you like to perform? (optimization/migration): ").lower()

        conversation_manager = ConversationManager(
            suggestion_engine=suggestion_engine, 
            migration_module=migration_module,
            task=task
        )

    except ValueError as e:
        logging.error(f"Initialization failed: {e}")
        print(f"Error: {e}. Please ensure your OPENAI_API_KEY is set correctly in a .env file.")
        return

    print("AI Campaign Assistant is ready. Type 'exit' or 'quit' to end the conversation.")
    print("-" * 70)
    
    ui = CliInterface()
    
    # Start the conversation
    initial_message = "Hello, I need help with campaign optimization."
    if task == "migration":
        initial_message = "Hello, I want to migrate a campaign."
        
    ai_response = conversation_manager.handle_message(initial_message)
    ui.display_response(ai_response)

    # 2. Main chat loop
    while True:
        user_message = ui.get_user_input()
        if user_message.lower() in ["exit", "quit"]:
            ui.display_response("Goodbye!")
            break
        
        ai_response = conversation_manager.handle_message(user_message)
        ui.display_response(ai_response)

if __name__ == "__main__":
    main()