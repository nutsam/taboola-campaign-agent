import openai
import logging
import os
from dotenv import load_dotenv
from core.prompt_template import SYSTEM_PROMPT, SUGGESTION_FORMATTING_PROMPT_TEMPLATE
from core.error_handler import error_handler, ApiError, SystemError

load_dotenv()

class ResponseGenerator:
    """
    Generates natural language responses based on structured data.
    """

    def __init__(self):
        openai.api_key = os.getenv("OPENAI_API_KEY")
        if not openai.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set.")


    def format_suggestions(self, suggestions: list[str]) -> str:
        """
        Uses the LLM to format the suggestions into a natural, persuasive response.
        """
        try:
            prompt = SUGGESTION_FORMATTING_PROMPT_TEMPLATE.format(suggestions)

            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
            )
            return response.choices[0].message['content']
        except Exception as e:
            error = ApiError(str(e), api_name="OpenAI", context={
                "model": "gpt-4o-mini",
                "operation": "format_suggestions"
            })
            error_message = error_handler.handle_error(error)
            # Provide fallback with raw suggestions
            fallback = "I've gathered some suggestions for you, but I'm having trouble formatting them nicely. Here is the raw data:\n" + "\n".join(suggestions)
            return f"{error_message}\n\n{fallback}"

    def format_migration_report(self, report) -> str:
        """
        Formats the migration report into a user-friendly string.
        """
        return f"Migration Report:\nSuccesses: {report.successes}\nWarnings: {report.warnings}\nFailures: {report.failures}"

    def get_response(self, conversation_history, functions):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=conversation_history,
                functions=functions,
                function_call="auto",
            )
            return response.choices[0].message
        except Exception as e:
            error = ApiError(str(e), api_name="OpenAI", context={"model": "gpt-4o-mini"})
            error_message = error_handler.handle_error(error)
            return {"content": error_message}

    def get_response_after_function_call(self, conversation_history, response_message, function_name, content):
        """
        Calls the LLM with the result of a function call and returns the response.
        """
        try:
            updated_history = conversation_history + [response_message, {"role": "function", "name": function_name, "content": content}]
            
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=updated_history,
            )
            return response.choices[0].message['content']
        except Exception as e:
            error = ApiError(str(e), api_name="OpenAI", context={
                "model": "gpt-4o-mini",
                "function_name": function_name,
                "operation": "function_call_response"
            })
            return error_handler.handle_error(error)
