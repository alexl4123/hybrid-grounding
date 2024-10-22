# pylint: disable=E1124
"""
Main Entry Point into the heuristic_splitter.
Parses arguments.
"""

import time
import argparse
import sys

from heuristic_splitter.heuristic_strategy import HeuristicStrategy
from heuristic_splitter.heuristic_splitter import HeuristicSplitter
from heuristic_splitter.grounding_strategy import GroundingStrategy

from heuristic_splitter.treewidth_computation_strategy import TreewidthComputationStrategy

def main():
    """
    Main Entry Point into the prototype.
    Parses arguments and calls heurstic_splitter class.
    """

    grounding_strategies = {
        "FULL": {
            "cmd_line": "full",
            "enum_mode": GroundingStrategy.FULL
            },
        "SUGGEST_USAGE": {
            "cmd_line": "suggest-bdg-usage",
            "enum_mode": GroundingStrategy.SUGGEST_USAGE,
        },
    }

    heuristic_methods = {
        "VARIABLE": {
            "cmd_line": "variable",
            "enum_mode": HeuristicStrategy.VARIABLE
            },
        "TREEWIDTH_PURE": {
            "cmd_line": "treewidth-pure",
            "enum_mode": HeuristicStrategy.TREEWIDTH_PURE,
        },
    }


    treewidth_strategies = {
        "NETWORKX": {
            "cmd_line": "networkx",
            "enum_mode": TreewidthComputationStrategy.NETWORKX_HEUR
            },
        "TWALGOR": {
            "cmd_line": "twalgor-exact",
            "enum_mode": TreewidthComputationStrategy.TWALGOR_EXACT,
        },
    }



    parser = argparse.ArgumentParser(prog="heuristic", usage="%(prog)s [files]")
    parser.add_argument(
        "--heuristic-method",
        default=heuristic_methods["TREEWIDTH_PURE"]["cmd_line"],
        choices=[
            heuristic_methods[key]["cmd_line"]
            for key in heuristic_methods.keys()
        ],
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print debug information.",
    )

    parser.add_argument(
        "--treewidth-strategy",
        default=treewidth_strategies["NETWORKX"]["cmd_line"],
        choices=[
            treewidth_strategies[key]["cmd_line"]
            for key in treewidth_strategies.keys()
        ],
    )
    parser.add_argument(
        "--grounding-strategy",
        default=grounding_strategies["FULL"]["cmd_line"],
        choices=[
            grounding_strategies[key]["cmd_line"]
            for key in grounding_strategies.keys()
        ],
    )
 



    parser.add_argument("files", type=argparse.FileType("r"), nargs="+")
    args = parser.parse_args()

    heuristic_method = None
    for key in heuristic_methods.keys():
        if args.heuristic_method == heuristic_methods[key]["cmd_line"]:
            heuristic_method = heuristic_methods[key]["enum_mode"]

    treewidth_strategy = None
    for key in treewidth_strategies.keys():
        if args.treewidth_strategy == treewidth_strategies[key]["cmd_line"]:
            treewidth_strategy = treewidth_strategies[key]["enum_mode"]

    grounding_strategy = None
    for key in grounding_strategies.keys():
        if args.grounding_strategy == grounding_strategies[key]["cmd_line"]:
            grounding_strategy = grounding_strategies[key]["enum_mode"]

    debug_mode = args.debug


    files = args.files
    #files = [open("TEST/190_heur.lp", "r")]
    contents = []
    for f in files:
        contents += f.readlines()

    start_time = time.time()
    heuristic = HeuristicSplitter(
        heuristic_method,
        treewidth_strategy,
        grounding_strategy,
        debug_mode,
    )
    heuristic.start(contents)

    end_time = time.time()
    if debug_mode is True:
        print(f"--> Total elapsed time for generation: {end_time - start_time}")
