import logging
from fastapi import FastAPI
from pydantic import BaseModel

# Core logic imports
from core.optimization_suggestion_engine.optimization_suggestion_engine import OptimizationSuggestionEngine
from core.conversation_manager.conversation_manager import ConversationManager
from core.migration_module.migration_module import MigrationModule, MigrationReport
from core.data_processor.data_processor import DataProcessor
from response_generator.response_generator import ResponseGenerator

# API client imports
from external.api_clients import (
    TaboolaHistoricalDataClient,
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

logging.info("Initializing API clients and core modules...")

# API Clients
historical_data_client = TaboolaHistoricalDataClient()
taboola_client = TaboolaApiClient()
facebook_client = FacebookApiClient()
source_clients = {'facebook': facebook_client}

# Core Modules
suggestion_engine = OptimizationSuggestionEngine(historical_data_client=historical_data_client)
migration_module = MigrationModule(taboola_client=taboola_client, source_clients=source_clients)
data_processor = DataProcessor(historical_data_client=historical_data_client)
response_generator = ResponseGenerator()

# NOTE: The /v1/chat endpoint is stateful and uses a single global conversation_manager instance.
# This is for demonstration purposes only. In a production environment, you would need
# a more robust session management system to handle concurrent conversations.
# This instance is configured for the 'optimization' task.
conversation_manager = ConversationManager(
    suggestion_engine=suggestion_engine,
    migration_module=migration_module, # Required for the combined ConversationManager
    data_processor=data_processor,
    response_generator=response_generator,
    task='optimization'
)

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
    Handles a user message in a conversation for campaign optimization.
    This endpoint is stateful and for demonstration purposes.
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