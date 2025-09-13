import logging
from ..prompt_template import SYSTEM_PROMPT
from ..optimization_suggestion_engine.optimization_suggestion_engine import OptimizationSuggestionEngine
from external.api_clients import NlpApiClient

class ConversationManager:
    """
    Manages the conversation flow with the advertiser, using an LLM and a system prompt.
    """

    def __init__(self, suggestion_engine: OptimizationSuggestionEngine, nlp_client: NlpApiClient):
        """
        Initializes the Conversation Manager with dependency-injected clients.
        """
        self.suggestion_engine = suggestion_engine
        self.nlp_client = nlp_client
        self.conversation_history = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
        self.collected_inputs = {}
        logging.info("ConversationManager initialized with injected NLP client.")

    def handle_message(self, user_message: str) -> str:
        """
        Handles a new message from the user by parsing it and advancing the conversation state.
        """
        logging.info(f"\nUser message: '{user_message}'")
        self.conversation_history.append({"role": "user", "content": user_message})

        # Use the NLP client to understand the user's message
        parsed_result = self.nlp_client.parse_intent_and_entities(user_message)
        intent = parsed_result.get('intent')
        entities = parsed_result.get('entities', {})

        ai_response = ""
        # This logic now uses the parsed intent to decide the next action.
        if not self.collected_inputs.get('url'):
            if intent == 'provide_url':
                self.collected_inputs['url'] = entities.get('url', "[URL not parsed]")
                ai_response = f"Thanks for the URL. What is your daily budget for this campaign?"
            else:
                ai_response = "Hello! To get started, what is the website or landing page you will be promoting?"

        elif not self.collected_inputs.get('budget'):
            if intent == 'provide_budget':
                self.collected_inputs['budget'] = entities.get('budget')
                ai_response = "Got it. What is your target Cost Per Action, or CPA?"
            else:
                ai_response = "I didn't catch a budget number. Could you please provide the daily budget?"

        elif not self.collected_inputs.get('cpa'):
            if intent == 'provide_cpa':
                self.collected_inputs['cpa'] = entities.get('cpa')
                ai_response = "Perfect. And which platform are you targeting? (e.g., Desktop, Mobile, or All)"
            else:
                ai_response = "I didn't catch a CPA value. Could you please provide your target CPA?"

        elif not self.collected_inputs.get('target_platform'):
            if intent == 'provide_platform':
                self.collected_inputs['target_platform'] = entities.get('platform', 'All')
                confirmation_message = (f"Excellent. Here's what I have:\n" 
                                    f"- URL: {self.collected_inputs['url']}\n" 
                                    f"- Daily Budget: ${self.collected_inputs['budget']}\n" 
                                    f"- Target CPA: ${self.collected_inputs['cpa']}\n" 
                                    f"- Target Platform: {self.collected_inputs['target_platform']}\n" 
                                    f"Is this all correct?")
                logging.info(f"AI asks for confirmation: {confirmation_message}")
                logging.info("User confirms: Yes, looks good.")
                analysis_message = "Thank you. I'm now analyzing this against our database... this might take a moment."
                logging.info(f"AI says: {analysis_message}")
                suggestions = self.suggestion_engine.get_suggestions(self.collected_inputs)
                ai_response = self._format_suggestions_with_llm(suggestions)
            else:
                ai_response = "I didn't catch a platform. Please specify if you are targeting Desktop, Mobile, or All."

        else:
            ai_response = "I've already provided the initial suggestions. Would you like to refine any parameters or start over?"

        self.conversation_history.append({"role": "assistant", "content": ai_response})
        return ai_response

    def _format_suggestions_with_llm(self, suggestions: list[str]) -> str:
        header = "I've analyzed the data, and here are a few suggestions based on top-performing campaigns in your domain:\n"
        formatted_list = []
        for suggestion in suggestions:
            if "targeting" in suggestion:
                formatted_list.append(f"**Targeting Recommendation:** {suggestion} We've seen that this specific demographic has a significantly higher conversion rate for similar products.")
            elif "budget" in suggestion:
                formatted_list.append(f"**Budget Recommendation:** {suggestion} Based on the data, this level of investment is more likely to give you the reach needed to hit your goals.")
        if not formatted_list:
            return "I've analyzed the data, but I couldn't find any specific recommendations based on the information provided."
        return header + "\n- " + "\n- ".join(formatted_list)
