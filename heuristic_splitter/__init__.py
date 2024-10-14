# pylint: disable=E1124
"""
Main Entry Point into the heuristic_splitter.
Parses arguments.
"""

import argparse
import sys

from heuristic_splitter.heuristic_strategy import HeuristicStrategy
from heuristic_splitter.heuristic_splitter import HeuristicSplitter

def main():
    """
    Main Entry Point into the prototype.
    Parses arguments and calls heurstic_splitter class.
    """


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



    parser = argparse.ArgumentParser(prog="heuristic", usage="%(prog)s [files]")
    parser.add_argument(
        "--heuristic-method",
        default=HeuristicStrategy.VARIABLE,
        choices=[
            heuristic_methods[key]["cmd_line"]
            for key in heuristic_methods.keys()
        ],
    )

    parser.add_argument("files", type=argparse.FileType("r"), nargs="+")
    args = parser.parse_args()

    heuristic_method = None
    for key in heuristic_methods.keys():
        if args.heuristic_method == heuristic_methods[key]["cmd_line"]:
            heuristic_method = heuristic_methods[key]["enum_mode"]

    contents = ""
    for f in args.files:
        contents += f.read()

    heuristic = HeuristicSplitter(
        HeuristicStrategy
    )
    heuristic.start(contents)
