# Campaign Assistant Architecture Overview

## Core Modules (`core/`)

### 1. Conversation Manager (`conversation_manager`)

* **Role**: Manages conversation flow, supporting optimization and migration tasks
* **Features**:

  * Uses OpenAI function calling to route user intents
* **Main Functions**:

  * `handle_message()` – Process user messages
  * `_process_function_call()` – Execute function calls
  * `_get_optimization_functions()` – Define optimization functions
  * `_get_migration_functions()` – Define migration functions

---

### 2. Data Processor (`data_processor`)

* **Role**: Validates user input data
* **Main Functions**:

  * `validate_url()` – URL format validation
  * `validate_budget()` – Budget range validation
  * `validate_cpa()` – CPA target validation
  * `validate_platform()` – Platform type validation

---

### 3. File Processor (`file_processor`)

* **Role**: Processes uploaded campaign files in multiple formats
* **Features**:

  * Dynamic schema validation for different platforms
* **Main Functions**:

  * `process_uploaded_file()` – Parse CSV/JSON/Excel files
  * `validate_campaign_data()` – Validate against platform schemas
  * `get_sample_format()` – Provide format examples
* **Components**:

  * **Schema Validator** – Dynamic validation

---

### 4. Optimization Suggestion Engine (`optimization_suggestion_engine`)

* **Role**: Generates optimization suggestions based on historical data
* **Main Functions**:

  * `get_suggestions()` – Generate campaign suggestions
  * `_find_similar_campaigns()` – Find similar campaigns
  * `_extract_patterns()` – Extract success patterns
  * `_generate_suggestions()` – Generate personalized suggestions

---

### 5. Migration Module (`migration_module`)

* **Role**: Cross-platform campaign migration
* **Main Functions**:

  * `migrate_campaign()` – Execute campaign migration
  * `map_to_taboola()` – Field mapping transformation
* **Adapters**:

  * `FacebookAdapter`
  * `TwitterAdapter`

---

### 6. Response Generator (`response_generator`)

* **Role**: AI response generation and formatting
* **Main Functions**:

  * `format_suggestions()` – Format suggestion responses
  * `format_migration_report()` – Format migration reports
  * `format_file_processing_result()` – Format file processing results
  * `format_validation_analysis()` – Generate AI-powered validation analysis
  * `get_response()` – Get AI response
  * `get_response_after_function_call()` – Response after function call

---

### 7. Error Handler (`error_handler`)

* **Role**: Unified error handling and user-friendly messaging
* **Main Functions**:

  * `handle_error()` – Central error handling
  * `_generate_user_message()` – Generate user-friendly messages
  * `get_error_stats()` – Error statistics
* **Features**:

  * Specialized handling methods for different error types

---

## External Integrations (`external/`)

### API Clients (`api_clients`)

* **Role**: Mock API implementations
* **Includes**:

  * `FacebookApiClient` – Facebook API client
  * `TwitterApiClient` – Twitter API client
  * `TaboolaApiClient` – Taboola API client
  * `TaboolaHistoricalDataClient` – Historical data client

---

## Application Entry Points

1. **Streamlit Web UI (`streamlit_chat.py`)**

   * Web-based real-time chat interface
   * Supports file upload functionality
   * Two task modes: optimization and migration
