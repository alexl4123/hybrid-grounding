
from enum import Enum

class GroundingStrategy(Enum):
    """
    Enum for different foundedness-strategies.
    """

    FULL = 1
    SUGGEST_USAGE = 2
    NON_GROUND_REWRITE = 3


