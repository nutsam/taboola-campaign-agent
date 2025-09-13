import openai
import logging
from core.prompt_template import SYSTEM_PROMPT, SUGGESTION_FORMATTING_PROMPT_TEMPLATE

class ResponseGenerator:
    """
    Generates natural language responses based on structured data.
    """

    def format_suggestions(self, suggestions: list[str]) -> str:
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

    def format_migration_report(self, report) -> str:
        """
        Formats the migration report into a user-friendly string.
        """
        return f"Migration Report:\nSuccesses: {report.successes}\nWarnings: {report.warnings}\nFailures: {report.failures}"