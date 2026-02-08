from enum import Enum


class UserLabels(str, Enum):
    USER = "User"
    PREFERENCE = "Preference"
    SESSION = "Session"
    SUMMARY = "Summary"
    INTERACTIOn = "Interaction"


class UserRelationships(str, Enum):
    HAS_PREFERENCE = "HAS_PREFERENCE"
    HAS_SESSION = "HAS_SESSION"
    HAS_SUMMARY = "HAS_SUMMARY"
    HAS_INTERACTION = "HAS_INTERACTION"
