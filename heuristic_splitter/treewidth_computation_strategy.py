
from enum import Enum

class TreewidthComputationStrategy(Enum):
    """
    Enum for different treewidth-strategies.
    """

    NETWORKX_HEUR = 1
    TWALGOR_EXACT = 2

