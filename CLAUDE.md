# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Application Overview

This is a **Taboola Campaign Assistant** - an AI-powered conversational application that helps advertisers with campaign optimization and cross-platform migration. The application uses OpenAI GPT-4o-mini for natural language processing with function calling capabilities.

## Core Architecture

The codebase follows a modular, layered architecture with dependency injection:

### Main Entry Points
- `chat_cli.py` - Command-line interface for terminal interaction
- `streamlit_chat.py` - Web-based Streamlit UI with real-time chat
- `app.py` - FastAPI application (appears to be under development)

### Core Modules (`core/`)
- **Conversation Manager** - Orchestrates chat flow using OpenAI function calling
- **Data Processor** - Validates user inputs (URLs, budgets, CPA values, platforms)
- **Generator** - Handles AI response generation via OpenAI API
- **Optimization Engine** - Analyzes historical Taboola data for campaign suggestions
- **Migration Module** - Cross-platform campaign migration with schema mapping
- **Error Handler** - Centralized error management with user-friendly messaging
- **Prompt Templates** - AI system prompts and conversation flow definitions

### External Integrations (`external/`)
- **API Clients** - Mock implementations for Taboola, Facebook, and Twitter APIs
- **API Contracts** - Abstract interfaces defining required API methods

## Development Commands

### Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables (add OPENAI_API_KEY to .env)
cp .env.example .env
```

### Running the Application
```bash
# CLI version
python chat_cli.py

# Web interface
streamlit run streamlit_chat.py

# FastAPI server (if implemented)
uvicorn app:app --reload
```

### Key Dependencies
- FastAPI (API framework)
- Streamlit >= 1.28.0 (Web UI)
- OpenAI (AI integration)
- Pydantic (Data validation)

## Architecture Patterns

### Function Calling System
The application uses OpenAI's function calling feature to route user intents to specific handlers:
- URL validation and analysis
- Budget optimization suggestions
- CPA (Cost Per Action) analysis
- Platform-specific campaign migration

### Migration System
Cross-platform campaign migration uses:
- **Platform Adapters**: Abstract adapters for different source platforms
- **Schema Mapping**: JSON-based field mapping configurations in `migration_module/schemas/`
- **Data Transformation**: Built-in functions like `divide_by_100`, `extract_creative_data`
- **Validation Pipeline**: Pydantic models ensure data integrity

### Error Handling
Centralized error management categorizes errors by type (Validation, API, Conversation) and provides user-friendly conversational responses while maintaining detailed logging.

## Code Organization Notes

- All core business logic is in the `core/` directory with clear module separation
- External API integrations are abstracted through interfaces in `external/`
- The generator system (recently added) handles AI response formatting
- Migration schemas are defined as JSON configurations for easy platform extensions
- Conversation flows are template-driven for consistent AI behavior

## Development Notes

- The application uses dependency injection throughout for testability
- All API clients are currently mock implementations
- Environment variables are managed through python-dotenv
- The codebase supports both CLI and web interfaces simultaneously
- Recent changes include UI additions and folder restructuring (see git history)