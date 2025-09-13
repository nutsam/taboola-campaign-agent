import logging
import os
import openai
import json
from dotenv import load_dotenv
from ..prompt_template import (
    SYSTEM_PROMPT,
    OPTIMIZATION_TASK_PROMPT,
    MIGRATION_TASK_PROMPT,
    SUGGESTION_FORMATTING_PROMPT_TEMPLATE
)
from ..optimization_suggestion_engine.optimization_suggestion_engine import OptimizationSuggestionEngine

load_dotenv()

class ConversationManager:
    """
    Manages the conversation flow with the advertiser, using an LLM and a system prompt.
    """

    def __init__(self, suggestion_engine: OptimizationSuggestionEngine, migration_module, task: str = 'optimization'):
        """
        Initializes the Conversation Manager.
        """
        self.suggestion_engine = suggestion_engine
        self.migration_module = migration_module
        
        if task == 'optimization':
            task_prompt = OPTIMIZATION_TASK_PROMPT
        elif task == 'migration':
            task_prompt = MIGRATION_TASK_PROMPT
        else:
            raise ValueError(f"Unknown task: {task}")

        self.conversation_history = [
            {"role": "system", "content": SYSTEM_PROMPT + task_prompt}
        ]
        
        openai.api_key = os.getenv("OPENAI_API_KEY")
        if not openai.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set.")
        logging.info(f"ConversationManager initialized for task: {task}")

        self.functions = [
            {
                "name": "create_campaign_suggestions",
                "description": "Gathers campaign details and creates optimization suggestions.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "The landing page URL for the campaign."
                        },
                        "budget": {
                            "type": "number",
                            "description": "The daily budget for the campaign."
                        },
                        "cpa": {
                            "type": "number",
                            "description": "The target Cost Per Action (CPA) for the campaign."
                        },
                        "target_platform": {
                            "type": "string",
                            "description": "The platform to target (e.g., Desktop, Mobile, All)."
                        }
                    },
                    "required": ["url", "budget", "cpa", "target_platform"]
                }
            },
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

    def handle_message(self, user_message: str) -> str:
        """
        Handles a new message from the user by calling the LLM and managing conversation state.
        """
        # logging.info(f"\nUser message: '{user_message}'")
        self.conversation_history.append({"role": "user", "content": user_message})

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=self.conversation_history,
                functions=self.functions,
                function_call="auto",
            )
            response_message = response.choices[0].message

            if response_message.get("function_call"):
                function_name = response_message["function_call"]["name"]
                if function_name == "create_campaign_suggestions":
                    function_args = json.loads(response_message["function_call"]["arguments"])
                    logging.info(f"Function call received: {function_name} with args {function_args}")
                    
                    suggestions = self.suggestion_engine.get_suggestions(function_args)
                    suggestion_response = self._format_suggestions_with_llm(suggestions)
                    
                    self.conversation_history.append(response_message)
                    self.conversation_history.append(
                        {
                            "role": "function",
                            "name": function_name,
                            "content": suggestion_response, 
                        }
                    )
                    return suggestion_response
                elif function_name == "migrate_campaign":
                    function_args = json.loads(response_message["function_call"]["arguments"])
                    logging.info(f"Function call received: {function_name} with args {function_args}")
                    
                    report = self.migration_module.migrate_campaign(
                        source_platform=function_args.get("source_platform"),
                        campaign_id=function_args.get("campaign_id")
                    )
                    
                    report_str = f"Migration Report:\nSuccesses: {report.successes}\nWarnings: {report.warnings}\nFailures: {report.failures}"
                    
                    self.conversation_history.append(response_message)
                    self.conversation_history.append(
                        {
                            "role": "function",
                            "name": function_name,
                            "content": report_str,
                        }
                    )
                    return report_str
            
            ai_response = response_message["content"]
            self.conversation_history.append({"role": "assistant", "content": ai_response})
            return ai_response

        except Exception as e:
            logging.error(f"Error calling OpenAI API: {e}")
            return "I'm sorry, I'm having trouble connecting to my brain right now. Please try again in a moment."

    def _format_suggestions_with_llm(self, suggestions: list[str]) -> str:
        """
        Uses the LLM to format the suggestions into a natural, persuasive response.
        """
        prompt = SUGGESTION_FORMATTING_PROMPT_TEMPLATE.format(suggestions)

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
            )
            formatted_suggestions = response.choices[0].message['content']
        except Exception as e:
            logging.error(f"Error calling OpenAI API for formatting: {e}")
            formatted_suggestions = "I've gathered some suggestions for you, but I'm having trouble formatting them nicely. Here is the raw data:\n" + "\n".join(suggestions)

        return formatted_suggestions
