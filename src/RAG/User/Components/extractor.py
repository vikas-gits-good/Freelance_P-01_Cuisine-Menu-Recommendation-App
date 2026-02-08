from typing import List

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, AnyMessage

from src.RAG.User.schemas import ExtractedPreferences

from src.Logging.logger import log_flk
from src.Exception.exception import LogException

EXTRACTOR_SYSTEM_PROMPT = """You extract user preferences from restaurant/cuisine conversations.

Analyze the latest user message and AI response. Extract any preferences as structured data.

CATEGORIES (use these exact values):
- cuisine_like: Cuisines the user likes (e.g. "Italian", "North Indian")
- cuisine_dislike: Cuisines the user dislikes (e.g. "Chinese")
- budget: Price preference (e.g. "low", "mid", "premium")
- dietary: Dietary restrictions (e.g. "vegetarian", "vegan", "halal", "non-veg")
- area_focus: Areas/localities of interest (e.g. "Koramangala", "Indiranagar")
- spice_level: Spice preference (e.g. "mild", "medium", "hot")
- meal_type: Meal type preference (e.g. "breakfast", "lunch", "dinner", "snacks")
- chain_preference: Chain vs independent (e.g. "chain", "independent")

CONFIDENCE SCORING:
- 1.0: User explicitly stated it ("I'm vegetarian", "I love Italian food")
- 0.7: Strongly implied (asked for vegetarian restaurants multiple times)
- 0.4: Weakly implied (mentioned once in passing)

RULES:
- Only extract preferences actually present in the conversation
- Return empty list if no preferences are detected
- Use lowercase for values
- Be conservative — only extract what is clearly there"""


class PreferenceExtractor:
    """Extracts user preferences from conversation using LLM structured output."""

    def __init__(self, llm: ChatGroq):
        self.llm = llm.with_structured_output(schema=ExtractedPreferences)

    def extract(self, messages: List[AnyMessage]) -> ExtractedPreferences:
        """Extract preferences from the latest conversation turn.

        Args:
            messages: Full conversation messages list.

        Returns:
            ExtractedPreferences with list of detected preferences.
        """
        try:
            convo = [
                SystemMessage(content=EXTRACTOR_SYSTEM_PROMPT),
                *messages[-2:],  # latest user query + AI response
            ]
            result: ExtractedPreferences = self.llm.invoke(convo)
            return result

        except Exception as e:
            LogException(e, logger=log_flk)
            return ExtractedPreferences()
