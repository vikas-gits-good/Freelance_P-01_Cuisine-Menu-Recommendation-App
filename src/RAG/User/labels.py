from enum import Enum


class UserLabels(str, Enum):
    USER = "User"
    PREFERENCE = "Preference"
    SESSION = "Session"
    SUMMARY = "Summary"
    INTERACTION = "Interaction"


class UserRelationships(str, Enum):
    HAS_PREFERENCE = "HAS_PREFERENCE"
    HAS_SESSION = "HAS_SESSION"
    HAS_SUMMARY = "HAS_SUMMARY"
    HAS_INTERACTION = "HAS_INTERACTION"


class PreferenceCategory(str, Enum):
    CUISINE_LIKE = "cuisine_like"
    CUISINE_DISLIKE = "cuisine_dislike"
    BUDGET = "budget"
    DIETARY = "dietary"
    AREA_FOCUS = "area_focus"
    SPICE_LEVEL = "spice_level"
    MEAL_TYPE = "meal_type"
    CHAIN_PREFERENCE = "chain_preference"
