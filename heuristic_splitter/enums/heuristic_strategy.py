
from enum import Enum

class HeuristicStrategy(Enum):
    """
    Enum for different foundedness-strategies.
    """

    VARIABLE = 1
    TREEWIDTH_PURE = 2

