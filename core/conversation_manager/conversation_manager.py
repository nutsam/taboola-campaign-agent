import logging
import os
import json
from dotenv import load_dotenv
from ..prompt_template import (
    SYSTEM_PROMPT,
    OPTIMIZATION_TASK_PROMPT,
    MIGRATION_TASK_PROMPT
)
from ..optimization_suggestion_engine.optimization_suggestion_engine import OptimizationSuggestionEngine
from ..data_processor.data_processor import DataProcessor
from ..error_handler import error_handler, ConversationError, ApiError

load_dotenv()

class ConversationManager:
    """
    Manages the conversation flow for both optimization and migration tasks.
    """

    def __init__(self, suggestion_engine: OptimizationSuggestionEngine, migration_module, data_processor: DataProcessor, response_generator, task: str):
        """
        Initializes the Conversation Manager for a specific task.
        """
        self.suggestion_engine = suggestion_engine
        self.migration_module = migration_module
        self.data_processor = data_processor
        self.response_generator = response_generator
        self.task = task
        self.collected_inputs = {}

        if task == 'optimization':
            task_prompt = OPTIMIZATION_TASK_PROMPT
            self.functions = self._get_optimization_functions()
        elif task == 'migration':
            task_prompt = MIGRATION_TASK_PROMPT
            self.functions = self._get_migration_functions()
        else:
            raise ValueError(f"Unknown task: {task}")

        self.conversation_history = [
            {"role": "system", "content": SYSTEM_PROMPT + task_prompt}
        ]

        logging.info(f"ConversationManager initialized for task: {task}")

    def handle_message(self, user_message: str) -> str:
        """
        Handles a new message from the user by calling the LLM and managing conversation state.
        """
        try:
            if not user_message or not user_message.strip():
                error = ConversationError("Empty message received", state=self.task)
                return error_handler.handle_error(error)
                
            self.conversation_history.append({"role": "user", "content": user_message})

            response_message = self.response_generator.get_response(self.conversation_history, self.functions)

            if response_message.get("function_call"):
                return self._process_function_call(response_message)

            ai_response = response_message["content"]
            self.conversation_history.append({"role": "assistant", "content": ai_response})
            return ai_response
            
        except Exception as e:
            return error_handler.handle_error(e, context={
                "operation": "handle_message",
                "task": self.task,
                "message_length": len(user_message) if user_message else 0
            })

    def _process_function_call(self, response_message):
        function_name = response_message["function_call"]["name"]
        function_args = json.loads(response_message["function_call"]["arguments"])
        logging.info(f"Function call received: {function_name} with args {function_args}")

        if function_name == 'process_url':
            is_valid, feedback = self.data_processor.validate_url(function_args.get('url'))
            if is_valid:
                self.collected_inputs['url'] = function_args.get('url')
                feedback = "URL validated successfully. Please provide your daily budget."
            
        elif function_name == 'process_budget':
            is_valid, feedback = self.data_processor.validate_budget(function_args.get('budget'))
            if is_valid:
                self.collected_inputs['budget'] = function_args.get('budget')
                feedback = "Budget validated successfully. Please provide your target CPA."

        elif function_name == 'process_cpa':
            is_valid, feedback = self.data_processor.validate_cpa(function_args.get('cpa'))
            if is_valid:
                self.collected_inputs['cpa'] = function_args.get('cpa')
                feedback = "CPA validated successfully. Please provide your target platform."

        elif function_name == 'process_platform':
            is_valid, feedback = self.data_processor.validate_platform(function_args.get('platform'))
            if is_valid:
                self.collected_inputs['platform'] = function_args.get('platform')
                feedback = "Platform validated successfully. All inputs collected. Ready to create suggestions."

        elif function_name == "create_campaign_suggestions":
            # All inputs should already be collected and validated
            suggestions = self.suggestion_engine.get_suggestions(self.collected_inputs)
            feedback = self.response_generator.format_suggestions(suggestions)

        elif function_name == "migrate_campaign":
            report = self.migration_module.migrate_campaign(
                source_platform=function_args.get("source_platform"),
                campaign_id=function_args.get("campaign_id")
            )
            feedback = self.response_generator.format_migration_report(report)

        # Add function call and result to conversation history
        self.conversation_history.append(response_message)
        self.conversation_history.append({"role": "function", "name": function_name, "content": feedback})
        
        # Get AI response after function call
        response = self.response_generator.get_response_after_function_call(self.conversation_history, response_message, function_name, feedback)
        
        # Add AI response to conversation history
        self.conversation_history.append({"role": "assistant", "content": response})
        
        return response

    

    def _get_optimization_functions(self):
        return [
            {
                "name": "process_url",
                "description": "Processes the campaign URL provided by the user.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "The campaign URL."
                        }
                    },
                    "required": ["url"]
                }
            },
            {
                "name": "process_budget",
                "description": "Processes the campaign budget provided by the user.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "budget": {
                            "type": "number",
                            "description": "The campaign budget."
                        }
                    },
                    "required": ["budget"]
                }
            },
            {
                "name": "process_cpa",
                "description": "Processes the target CPA provided by the user.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "cpa": {
                            "type": "number",
                            "description": "The target CPA."
                        }
                    },
                    "required": ["cpa"]
                }
            },
            {
                "name": "process_platform",
                "description": "Processes the target platform provided by the user.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "platform": {
                            "type": "string",
                            "description": "The target platform (Desktop, Mobile, or Both)."
                        }
                    },
                    "required": ["platform"]
                }
            },
            {
                "name": "create_campaign_suggestions",
                "description": "Gathers all campaign details and creates optimization suggestions.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string"},
                        "budget": {"type": "number"},
                        "cpa": {"type": "number"},
                        "platform": {"type": "string"}
                    },
                    "required": ["url", "budget", "cpa", "platform"]
                }
            }
        ]

    def _get_migration_functions(self):
        return [
            {
                "name": "migrate_campaign",
                "description": "Migrates a campaign from a source platform to Taboola.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "source_platform": {
                            "type": "string",
                            "description": "The source platform of the campaign (e.g., facebook)."
                        },
                        "campaign_id": {
                            "type": "string",
                            "description": "The ID of the campaign to migrate."
                        }
                    },
                    "required": ["source_platform", "campaign_id"]
                }
            }
        ]
