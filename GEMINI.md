# GEMINI.md

## Project Overview

This project is the "AI Campaign Assistant API," a Python-based web service built with FastAPI. Its primary purpose is to assist with digital advertising campaigns by providing AI-powered optimization suggestions and facilitating campaign migration from other platforms to Taboola.

The application exposes a REST API with two main endpoints:
*   `/v1/chat`: A conversational endpoint for getting campaign optimization advice.
*   `/v1/migrate`: An endpoint to programmatically migrate campaigns from platforms like Facebook to Taboola.

The architecture is modular, with a clear separation of concerns between the API layer (`app.py`), core AI and business logic (`core/`), and external service integrations (`external_integrations/`).

## Building and Running

To run the application, follow these steps:

1.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run the server:**
    ```bash
    uvicorn app:app --reload
    ```

The API will be available at `http://127.0.0.1:8000`. Interactive documentation (Swagger UI) can be accessed at `http://127.0.0.1:8000/docs`.

## Development Conventions

*   **Modular Design:** The codebase is organized into distinct modules, each with a specific responsibility (e.g., `optimization_suggestion_engine`, `migration_module`).
*   **API Contracts:** The project uses abstract base classes in `external_integrations/taboola_api_contract.py` to define the interfaces for the Taboola APIs. The mock clients in `external_integrations/api_clients.py` implement these contracts.
*   **Adapter Pattern:** The `migration_module` uses the adapter pattern to handle campaign data from different source platforms. Each platform (e.g., Facebook, Twitter) has its own adapter that knows how to fetch and transform its data into a format compatible with Taboola.
*   **Logging:** The application uses the `logging` module to provide detailed information about its execution, which is helpful for debugging and tracing the flow of requests.

## Key Modules

*   **`app.py`**: The main entry point of the FastAPI application. It defines the API endpoints, initializes the core modules and API clients, and handles request/response models.
*   **`core/`**: This directory contains the core business logic of the application.
    *   `optimization_suggestion_engine.py`: Analyzes user campaign data and provides optimization suggestions based on historical data from successful Taboola campaigns.
    *   `migration_module.py`: Orchestrates the process of migrating campaigns from a source platform to Taboola. It uses platform-specific adapters to handle the data mapping.
    *   `conversation_manager.py`: Manages the state of the conversation for the chat endpoint.
*   **`external_integrations/`**: This directory contains the clients for interacting with external services.
    *   `api_clients.py`: Contains mock implementations of API clients for Facebook, Twitter, a generic NLP service, and the Taboola API.
    *   `taboola_api_contract.py`: Defines the interfaces that the Taboola API clients must implement.
