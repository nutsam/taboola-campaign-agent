# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Running the Application
```bash
# Install dependencies
pip install -r requirements.txt

# Start the FastAPI server
uvicorn app:app --reload

# The API will be available at http://127.0.0.1:8000
# Interactive documentation (Swagger UI) at http://127.0.0.1:8000/docs
```

### Testing API Endpoints
- POST `/v1/chat` - Stateful chat interface for campaign optimization
- POST `/v1/migrate` - Campaign migration from other platforms to Taboola
- GET `/` - Root endpoint with API status

## Architecture Overview

This is an AI-powered campaign assistant for Taboola advertising platform with two main workflows:

### Core Components
- **FastAPI Application** (`app.py`): Main API server with chat and migration endpoints
- **ConversationManager** (`core/conversation_manager/`): Handles stateful chat conversations for optimization and migration tasks
- **OptimizationSuggestionEngine** (`core/optimization_suggestion_engine/`): Generates campaign optimization suggestions based on historical data
- **MigrationModule** (`core/migration_module/`): Handles cross-platform campaign migration with schema transformation
- **DataProcessor** (`core/data_processor/`): Validates campaign inputs (budget, CPA, URLs) against historical benchmarks
- **ResponseGenerator** (`response_generator/`): Formats AI responses using OpenAI API

### API Integration Layer
- **External API Clients** (`external/api_clients.py`): Mock implementations for Facebook, Twitter, and Taboola APIs
- **API Contracts** (`external/taboola_api_contract.py`): Interface definitions for Taboola API integration

### Data Flow
1. **Optimization Flow**: User provides campaign URL, budget, CPA, target platform → System validates inputs → Generates optimization suggestions based on historical data
2. **Migration Flow**: User provides source platform and campaign ID → System fetches campaign data → Transforms schema → Creates campaign in Taboola

### Key Features
- Stateful conversation management with task-specific prompts
- Historical data analysis for campaign optimization
- Cross-platform schema mapping (Facebook/Twitter → Taboola)
- Input validation against performance benchmarks
- OpenAI-powered natural language responses

### Environment Variables
Ensure `.env` file contains OpenAI API key for the ResponseGenerator to function properly.

## Error Handling System

### Comprehensive Error Management
The system includes a robust error handling framework that manages:

- **Error Categorization**: Validation, API, Conversation, Data Processing, Migration, Optimization, and System errors
- **Error Logging**: Dedicated logging to `campaign_assistant_errors.log` with structured context
- **Error Recovery**: Automatic retry mechanisms and graceful fallback strategies
- **User-Friendly Messages**: Context-aware error messages appropriate for end users

### Error Types and Handling
- **ValidationError**: Input validation failures (URL, budget, CPA, platform)
- **ApiError**: External API failures (OpenAI, Taboola, Facebook)
- **ConversationError**: Chat flow and state management issues
- **DataProcessingError**: Data transformation and processing failures
- **MigrationError**: Campaign migration failures
- **OptimizationError**: Suggestion generation failures
- **SystemError**: Critical system-level failures

### Error Recovery Features
- **Automatic Retry**: Configurable retry with exponential backoff for transient failures
- **Fallback Mechanisms**: Alternative approaches when primary methods fail
- **Input Suggestions**: Helpful suggestions for fixing validation errors
- **Graceful Degradation**: Maintain basic functionality during partial system failures

### Testing Error Handling
```bash
# Run comprehensive error handling tests
python test_error_handling.py
```

### Note on API Clients
Current API clients are mock implementations for demonstration. Real integrations would require actual API credentials and endpoint implementations following the contracts in `taboola_api_contract.py`.