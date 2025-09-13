import openai
import logging
import os
from dotenv import load_dotenv
from core.prompt_template import SYSTEM_PROMPT, SUGGESTION_FORMATTING_PROMPT_TEMPLATE

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
        prompt = SUGGESTION_FORMATTING_PROMPT_TEMPLATE.format(suggestions)

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
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
            logging.error(f"Error calling OpenAI API: {e}")
            return {"content": "I'm sorry, I'm having trouble connecting to my brain right now. Please try again in a moment."}

    def get_response_after_function_call(self, conversation_history, response_message, function_name, content):
        """
        Calls the LLM with the result of a function call and returns the response.
        """
        updated_history = conversation_history + [response_message, {"role": "function", "name": function_name, "content": content}]
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=updated_history,
            )
            return response.choices[0].message['content']
        except Exception as e:
            logging.error(f"Error calling OpenAI API after function call: {e}")
            return "I'm sorry, I'm having trouble processing the results. Please try again."
