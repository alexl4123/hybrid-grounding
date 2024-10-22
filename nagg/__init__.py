# pylint: disable=E1124
"""
Main Entry Point into the prototype.
Parses arguments and calls nagg class.
"""

import time
import argparse
import sys

from .aggregate_transformer import AggregateMode
from .cyclic_strategy import CyclicStrategy
from .default_output_printer import DefaultOutputPrinter
from .grounding_modes import GroundingModes
from .nagg import NaGG
from .foundedness_strategy import FoundednessStrategy

def main():
    """
    Main Entry Point into the prototype.
    Parses arguments and calls nagg class.
    """

    cyclic_choices = {
        "TIGHT": {"cmd_line": "assume-tight", "enum_mode": CyclicStrategy.ASSUME_TIGHT},
        "LVL-MAP": {
            "cmd_line": "level-mappings",
            "enum_mode": CyclicStrategy.LEVEL_MAPPING,
        },
        "SCBP": {
            "cmd_line": "shared-cycle-body-predicates",
            "enum_mode": CyclicStrategy.SHARED_CYCLE_BODY_PREDICATES,
        },
        "LVL-MAP-AAAI": {
            "cmd_line": "level-mappings-AAAI",
            "enum_mode": CyclicStrategy.LEVEL_MAPPING_AAAI,
        },
    }

    aggregate_choices = {
        "RA": {"cmd_line": "RA", "enum_mode": AggregateMode.RA},
        "RS": {"cmd_line": "RS", "enum_mode": AggregateMode.RS},
        "RS_PLUS": {"cmd_line": "RS-PLUS", "enum_mode": AggregateMode.RS_PLUS},
        "RS_STAR": {"cmd_line": "RS-STAR", "enum_mode": AggregateMode.RS_STAR},
        "RECURSIVE": {"cmd_line": "RECURSIVE", "enum_mode": AggregateMode.RECURSIVE},
    }

    grounding_modes_choices = {
        "PAR": {
            "cmd_line": "rewrite-aggregates-ground-partly",
            "enum_mode": GroundingModes.REWRITE_AGGREGATES_GROUND_PARTLY,
        },
        "AGG": {
            "cmd_line": "rewrite-aggregates-no-ground",
            "enum_mode": GroundingModes.REWRITE_AGGREGATES_NO_GROUND,
        },
        "FUL": {
            "cmd_line": "rewrite-aggregates-ground-fully",
            "enum_mode": GroundingModes.REWRITE_AGGREGATES_GROUND_FULLY,
        },
    }

    foundedness_choices = {
        "SATURATION": {
            "cmd_line": "saturation",
            "enum_mode": FoundednessStrategy.SATURATION,
        },
        "DEFAULT": {
            "cmd_line": "default",
            "enum_mode": FoundednessStrategy.DEFAULT,
        },
    }

    parser = argparse.ArgumentParser(prog="nagg", usage="%(prog)s [files]")
    parser.add_argument(
        "--no-show",
        action="store_true",
        help="Do not print #show-statements to avoid compatibility issues. ",
    )
    parser.add_argument(
        "--mode",
        default=GroundingModes.REWRITE_AGGREGATES_GROUND_PARTLY,
        choices=[
            grounding_modes_choices[key]["cmd_line"]
            for key in grounding_modes_choices.keys()
        ],
    )
    parser.add_argument(
        "--aggregate-strategy",
        default=aggregate_choices["RA"]["cmd_line"],
        choices=[
            aggregate_choices[key]["cmd_line"] for key in aggregate_choices.keys()
        ],
    )
    parser.add_argument(
        "--cyclic-strategy",
        default=cyclic_choices["TIGHT"]["cmd_line"],
        choices=[cyclic_choices[key]["cmd_line"] for key in cyclic_choices.keys()],
    )

    parser.add_argument(
        "--foundedness-strategy",
        default=foundedness_choices["DEFAULT"]["cmd_line"],
        choices=[foundedness_choices[key]["cmd_line"] for key in foundedness_choices.keys()],
    )

    parser.add_argument("files", type=argparse.FileType("r"), nargs="+")
    args = parser.parse_args()

    ground_guess = False
    no_show = False
    if args.no_show:
        sys.argv.remove("--no-show")
        no_show = True

    grounding_mode = None
    for key in grounding_modes_choices.keys():
        if args.mode == grounding_modes_choices[key]["cmd_line"]:
            grounding_mode = grounding_modes_choices[key]["enum_mode"]

    foundedness_strategy = None
    for key in foundedness_choices.keys():
        if args.foundedness_strategy == foundedness_choices[key]["cmd_line"]:
            foundedness_strategy = foundedness_choices[key]["enum_mode"]

    if (
        grounding_mode
        and grounding_mode == GroundingModes.REWRITE_AGGREGATES_GROUND_FULLY
    ):
        ground_guess = True

    aggregate_strategy = None
    for key in aggregate_choices.keys():
        if args.aggregate_strategy == aggregate_choices[key]["cmd_line"]:
            aggregate_strategy = aggregate_choices[key]["enum_mode"]

    normal_strategy = None
    for key in cyclic_choices.keys():
        if args.cyclic_strategy == cyclic_choices[key]["cmd_line"]:
            normal_strategy = cyclic_choices[key]["enum_mode"]

    contents = ""
    for f in args.files:
        contents += f.read()

    nagg = NaGG(
        no_show=no_show,
        ground_guess=ground_guess,
        output_printer=DefaultOutputPrinter(),
        aggregate_mode=aggregate_strategy,
        cyclic_strategy=normal_strategy,
        grounding_mode=grounding_mode,
        foundedness_strategy=foundedness_strategy,
    )
    nagg.start(contents)
