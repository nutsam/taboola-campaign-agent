import logging
from fastapi import FastAPI
from pydantic import BaseModel

# Core logic imports
from core_ai_logic.optimization_suggestion_engine import OptimizationSuggestionEngine
from core_ai_logic.conversation_manager import ConversationManager
from core_ai_logic.migration_module import MigrationModule, MigrationReport

# API client imports
from external_integrations.api_clients import (
    NlpApiClient,
    HistoricalDataApiClient,
    FacebookApiClient,
    TaboolaApiClient
)

# --- 1. App Configuration & Initialization ---

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI(
    title="AI Campaign Assistant API",
    description="An API for campaign optimization suggestions and cross-platform migration.",
    version="1.0.0"
)

# --- 2. Initialize all API Clients and Core Modules ---
# In a real app, these would be managed more robustly (e.g., with a dependency injection framework).
# For this demonstration, we'll create singleton instances here.

logging.info("Initializing API clients and core modules...")

# API Clients
nlp_client = NlpApiClient()
historical_data_client = HistoricalDataApiClient()
taboola_client = TaboolaApiClient()
facebook_client = FacebookApiClient()
source_clients = {'facebook': facebook_client}

# Core Modules
suggestion_engine = OptimizationSuggestionEngine(historical_data_client=historical_data_client)
migration_module = MigrationModule(taboola_client=taboola_client, source_clients=source_clients)

# NOTE: Storing conversation state in a global variable is not suitable for production.
# In a real-world scenario, you would use a session management system with a
# database or cache (like Redis) to store conversation history per user.
conversation_manager = ConversationManager(suggestion_engine=suggestion_engine, nlp_client=nlp_client)

logging.info("Initialization complete. Application is ready.")


# --- 3. Define Request and Response Models ---

class ChatRequest(BaseModel):
    user_message: str

class ChatResponse(BaseModel):
    ai_response: str

class MigrationRequest(BaseModel):
    source_platform: str
    campaign_id: str

class MigrationResponse(BaseModel):
    status: str
    report: dict

# --- 4. Define API Endpoints ---

@app.post("/v1/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Handles a user message in a conversation and returns the AI agent's response.
    This endpoint is stateful for demonstration purposes.
    """
    logging.info(f"Received chat request: {request.user_message}")
    ai_response = conversation_manager.handle_message(request.user_message)
    return ChatResponse(ai_response=ai_response)

@app.post("/v1/migrate", response_model=MigrationResponse)
async def migrate_endpoint(request: MigrationRequest):
    """
    Triggers a campaign migration from a source platform to Taboola.
    """
    logging.info(f"Received migration request for campaign '{request.campaign_id}' from '{request.source_platform}'")
    report = migration_module.migrate_campaign(
        source_platform=request.source_platform,
        campaign_id=request.campaign_id
    )
    # Convert the report object to a dictionary for the JSON response
    return MigrationResponse(
        status="Migration process finished.",
        report={
            "successes": report.successes,
            "warnings": report.warnings,
            "failures": report.failures
        }
    )

@app.get("/")
async def root():
    """Root endpoint providing basic information about the API."""
    return {"message": "AI Campaign Assistant API is running. See /docs for interactive documentation."}
