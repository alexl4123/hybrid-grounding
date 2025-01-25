
from enum import Enum

class CyclicStrategy(Enum):
    """
    Enum for different foundedness-strategies (cycles).
    """

    USE_SOTA = 1
    UNFOUND_SET = 2
    LEVEL_MAPPINGS = 3




