"""
Enum which depicts the different grounding modes.
"""
from enum import Enum


class GroundingModes(Enum):
    """
    Enum which depicts the different grounding modes.
    """
    RewriteAggregatesGroundPartly = 1
    RewriteAggregatesNoGround = 2
    RewriteAggregatesGroundFully = 3
