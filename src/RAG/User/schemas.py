from typing import List, Optional
from pydantic import BaseModel, Field


class PreferenceData(BaseModel):
    """Single extracted preference fact from conversation."""

    category: str = Field(description="Preference category (e.g. cuisine_like, dietary, budget)")
    value: str = Field(description="Preference value (e.g. Italian, vegetarian, mid)")
    confidence: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Confidence score: 1.0=explicit, 0.7=strong inference, 0.4=weak inference",
    )
    explicit: bool = Field(
        default=True,
        description="True if user explicitly stated it, False if inferred",
    )


class ExtractedPreferences(BaseModel):
    """LLM structured output for preference extraction."""

    preferences: List[PreferenceData] = Field(
        default_factory=list,
        description="List of user preferences extracted from the conversation turn",
    )


class InteractionData(BaseModel):
    """Data for a single conversation interaction."""

    query: str = Field(description="User's query text")
    intent: str = Field(default="gnrl_chat", description="Classified intent")
    tool_used: Optional[str] = Field(default=None, description="Tool used if any")
    result_brief: str = Field(default="", description="Brief summary of result")


class UserContext(BaseModel):
    """Formatted user context for injection into prompts."""

    preferences_text: str = Field(
        default="No preferences recorded yet.",
        description="Formatted preferences string for prompt injection",
    )
    summary_text: str = Field(
        default="No conversation history available.",
        description="Latest user summary for prompt injection",
    )
