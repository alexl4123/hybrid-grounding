import os
import sys
import argparse
import subprocess
import resource



import clingo

from datetime import datetime

from nagg.nagg import NaGG
from nagg.default_output_printer import DefaultOutputPrinter

from nagg.aggregate_strategies.aggregate_mode import AggregateMode

from nagg.cyclic_strategy import CyclicStrategy

from nagg.grounding_modes import GroundingModes

from .regression_test_mode import RegressionTestStrategy

from heuristic_splitter.heuristic_splitter import HeuristicSplitter

from heuristic_splitter.enums.heuristic_strategy import HeuristicStrategy
from heuristic_splitter.enums.treewidth_computation_strategy import TreewidthComputationStrategy
from heuristic_splitter.enums.grounding_strategy import GroundingStrategy
from heuristic_splitter.enums.output import Output

def limit_virtual_memory():
    max_virtual_memory = 1024 * 1024 * 1024 * 64 # 64GB

    # TUPLE -> (soft limit, hard limit)
    resource.setrlimit(resource.RLIMIT_AS, (max_virtual_memory, max_virtual_memory))


def block_print():
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.devnull, 'w')

def enable_print():
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__

class CustomOutputPrinter(DefaultOutputPrinter):

    def __init__(self):
        self.string = ""

    def custom_print(self, string):
        self.string = self.string + str(string) + '\n'

    def get_string(self):
        return self.string

class Context:
    def id(self, x):
        return x

    def seq(self, x, y):
        return [x, y]

class EquivChecker:

    def __init__(self, chosenRegressionTestMode, foundedness_strategy, log_file_tmp_prefix, heuristic_splitter_test = False):

        self.log_file_tmp_prefix = log_file_tmp_prefix

        self.chosenRegressiontestMode = chosenRegressionTestMode
        self.foundedness_strategy = foundedness_strategy
        self.heuristic_splitter_test = heuristic_splitter_test

        self.clingo_output = []
        self.nagg_output = []

        self.clingo_hashes = {}
        self.nagg_hashes = {}

    def on_model(self, m, output, hashes):
        symbols = m.symbols(shown=True)
        output.append([])
        cur_pos = len(output) - 1
        for symbol in symbols:
            output[cur_pos].append(str(symbol))

        output[cur_pos].sort()

        hashes[(hash(tuple(output[cur_pos])))] = cur_pos

    def parse(self):
        parser = argparse.ArgumentParser(prog='Answerset Equivalence Checker', description='Checks equivalence of answersets produced by nagg and clingo.')

        parser.add_argument('instance')
        parser.add_argument('encoding')
        args = parser.parse_args()

        instance_filename = args.instance
        encoding_filename = args.encoding

        if not os.path.isfile(instance_filename):
            print(f'Provided instance file \'{instance_filename}\' not found or is not a file')
            return
        if not os.path.isfile(encoding_filename):
            print(f'Provided encoding file \'{encoding_filename}\' not found or is not a file')
            return

        instance_file_contents = open(instance_filename, 'r').read()
        encoding_file_contents = open(encoding_filename, 'r').read()

        return (instance_file_contents, encoding_file_contents)



    def start(self, instance_file_contents, encoding_file_contents, verbose = True, one_directional_equivalence = True):
        """ 
            one_directional_equivalence: If True, then only the direction clingo -> nagg is checked, i.e. it must be the case, that for each answer set in the clingo result, there must be one in the nagg result as well (but therefore it could be, that nagg has more answersets)
        """

        gringo_encoding = []
        encoding_splits = encoding_file_contents.split("\n")
        for encoding_line in encoding_splits:
            if encoding_line.startswith("#program"):
                # Do not add lines to the encoding with #program lpopt|rules.
                continue
        
            gringo_encoding.append(encoding_line)

        gringo_encoding_contents = "\n".join(gringo_encoding)

        regression_test_strategy_string = ""

        if self.chosenRegressiontestMode == RegressionTestStrategy.AGGREGATES_RS_STAR or self.chosenRegressiontestMode == RegressionTestStrategy.AGGREGATES_RS_PLUS or self.chosenRegressiontestMode == RegressionTestStrategy.AGGREGATES_RS or self.chosenRegressiontestMode == RegressionTestStrategy.AGGREGATES_RA or self.chosenRegressiontestMode == RegressionTestStrategy.AGGREGATES_RECURSIVE:
            grounding_mode = GroundingModes.REWRITE_AGGREGATES_NO_GROUND
            cyclic_strategy = CyclicStrategy.ASSUME_TIGHT
            ground_guess = False

            regression_test_strategy_string = "Checking Aggregates "

            if self.chosenRegressiontestMode == RegressionTestStrategy.AGGREGATES_RS_STAR:
                aggregate_modes = [
                    ("RS-STAR", AggregateMode.RS_STAR)
                ]
                regression_test_strategy_string += "with RS-STAR strategy"
            elif self.chosenRegressiontestMode == RegressionTestStrategy.AGGREGATES_RS_PLUS:
                aggregate_modes = [
                    ("RS-PLUS", AggregateMode.RS_PLUS)
                ]
                regression_test_strategy_string += "with RS-PLUS strategy"
            elif self.chosenRegressiontestMode == RegressionTestStrategy.AGGREGATES_RS:
                aggregate_modes = [
                    ("RS", AggregateMode.RS)
                ]
                regression_test_strategy_string += "with RS strategy"
            elif self.chosenRegressiontestMode == RegressionTestStrategy.AGGREGATES_RA:
                aggregate_modes = [
                    ("RA", AggregateMode.RA)
                ]
                regression_test_strategy_string += "with RA strategy"
            elif self.chosenRegressiontestMode == RegressionTestStrategy.AGGREGATES_RECURSIVE:
                aggregate_modes = [
                    ("RECURSIVE", AggregateMode.RECURSIVE)
                ]
                regression_test_strategy_string += "with Recursive strategy"


        elif self.chosenRegressiontestMode == RegressionTestStrategy.REWRITING_TIGHT or self.chosenRegressiontestMode == RegressionTestStrategy.REWRITING_SHARED_CYCLE or self.chosenRegressiontestMode == RegressionTestStrategy.REWRITING_LEVEL_MAPPINGS_AAAI or self.chosenRegressiontestMode == RegressionTestStrategy.REWRITING_LEVEL_MAPPINGS: 
            aggregate_modes = [("RA", AggregateMode.RA)]
            grounding_mode = GroundingModes.REWRITE_AGGREGATES_GROUND_PARTLY
            ground_guess = False

            regression_test_strategy_string = "Checking nagg with partly rewriting "

            if self.chosenRegressiontestMode == RegressionTestStrategy.REWRITING_TIGHT:
                cyclic_strategy = CyclicStrategy.ASSUME_TIGHT
                regression_test_strategy_string += " with the assumption of tight programs."
            elif self.chosenRegressiontestMode == RegressionTestStrategy.REWRITING_SHARED_CYCLE:
                cyclic_strategy = CyclicStrategy.SHARED_CYCLE_BODY_PREDICATES
                regression_test_strategy_string += " with the rewriting-shared-cycle strategy for normal programs."
            elif self.chosenRegressiontestMode == RegressionTestStrategy.REWRITING_LEVEL_MAPPINGS_AAAI:
                cyclic_strategy = CyclicStrategy.LEVEL_MAPPING_AAAI
                regression_test_strategy_string += " with the level-mappings rewriting 1."
            elif self.chosenRegressiontestMode == RegressionTestStrategy.REWRITING_LEVEL_MAPPINGS:
                cyclic_strategy = CyclicStrategy.LEVEL_MAPPING
                regression_test_strategy_string += " with the level-mappings rewriting 2."

        elif self.chosenRegressiontestMode == RegressionTestStrategy.FULLY_GROUNDED_TIGHT or  self.chosenRegressiontestMode == RegressionTestStrategy.FULLY_GROUNDED_SHARED_CYCLE or self.chosenRegressiontestMode == RegressionTestStrategy.FULLY_GROUNDED_LEVEL_MAPPINGS_AAAI or self.chosenRegressiontestMode == RegressionTestStrategy.FULLY_GROUNDED_LEVEL_MAPPINGS:
        
            aggregate_modes = [("RA", AggregateMode.RA)]
            grounding_mode = GroundingModes.REWRITE_AGGREGATES_GROUND_FULLY
            ground_guess = True

            regression_test_strategy_string = "Checking nagg with fully rewriting "

            if self.chosenRegressiontestMode == RegressionTestStrategy.FULLY_GROUNDED_TIGHT:
                cyclic_strategy = CyclicStrategy.ASSUME_TIGHT
                regression_test_strategy_string += " with the assumption of tight programs."
            elif self.chosenRegressiontestMode == RegressionTestStrategy.FULLY_GROUNDED_SHARED_CYCLE:
                cyclic_strategy = CyclicStrategy.SHARED_CYCLE_BODY_PREDICATES
                regression_test_strategy_string += " with the rewriting-shared-cycle strategy for normal programs."
            elif self.chosenRegressiontestMode == RegressionTestStrategy.FULLY_GROUNDED_LEVEL_MAPPINGS_AAAI:
                cyclic_strategy = CyclicStrategy.LEVEL_MAPPING_AAAI
                regression_test_strategy_string += " with the level-mappings rewriting 1."
            elif self.chosenRegressiontestMode == RegressionTestStrategy.FULLY_GROUNDED_LEVEL_MAPPINGS:
                cyclic_strategy = CyclicStrategy.LEVEL_MAPPING
                regression_test_strategy_string += " with the level-mappings rewriting 2."
        else:
            raise Exception("REGRESSION TEST STRATEGY NOT IMPLEMENTED")

        print("<<<<<<<<<<>>>>>>>>>>")
        print(f"---- {regression_test_strategy_string} ----")
        print("<<<<<<<<<<>>>>>>>>>>")

        works = True
        no_show = False

        for aggregate_mode in aggregate_modes:

            print(f"[INFO] Checking current test with aggregate strategy: {aggregate_mode[0]}")

            combined_file_input = instance_file_contents + gringo_encoding_contents
            optimization_problem_clingo = self.start_clingo(combined_file_input, self.clingo_output, self.clingo_hashes, mode="clingo")

            # Custom printer keeps result of prototype (NaGG)
            custom_printer = CustomOutputPrinter()

            heuristic_strategy = HeuristicStrategy.TREEWIDTH_PURE
            treewidth_strategy = TreewidthComputationStrategy.NETWORKX_HEUR
            grounding_strategy = GroundingStrategy.FULL
            output_type = Output.DEFAULT_GROUNDER

            debug_mode = False

            enable_lpopt = True
            enable_logging = True

            current_datetime = datetime.now()
            log_file_name = self.log_file_tmp_prefix + "_" + current_datetime.strftime("%Y%m%d-%H%M%S") + ".log"

            if self.heuristic_splitter_test is False:
                total_content = instance_file_contents + "\n#program rules.\n" + encoding_file_contents

                heuristic_splitter = HeuristicSplitter(
                    heuristic_strategy, treewidth_strategy, grounding_strategy,
                    debug_mode, enable_lpopt, output_printer = custom_printer,
                    enable_logging=enable_logging, logging_file=log_file_name,
                    output_type=output_type
                )
                heuristic_splitter.start(total_content)

            else:
                heur_split_content = instance_file_contents + "\n" + encoding_file_contents

                heuristic_splitter = HeuristicSplitter(
                    heuristic_strategy, treewidth_strategy, grounding_strategy,
                    debug_mode, enable_lpopt, output_printer = custom_printer,
                    enable_logging=enable_logging, logging_file=log_file_name,
                    output_type=output_type
                )
                heuristic_splitter.start(heur_split_content)
            
            optimization_problem_nagg = self.start_clingo(custom_printer.get_string(), self.nagg_output, self.nagg_hashes, mode="clingo")

            if optimization_problem_clingo is not None and optimization_problem_nagg is not None:
                if optimization_problem_clingo != optimization_problem_nagg:
                    works = False
                    print(f"[ERROR] Final optimzed value clingo: {optimization_problem_clingo} vs. NaGG: {optimization_problem_nagg}")
            else:                    
                if not one_directional_equivalence and len(self.clingo_output) != len(self.nagg_output):
                    works = False
                else:
                    for clingo_key in self.clingo_hashes.keys():
                        if clingo_key not in self.nagg_hashes:
                            works = False
                            if verbose:
                                print(f"[ERROR] Used Aggregate Mode: {aggregate_mode[0]} - Could not find corresponding stable model in nagg for hash {clingo_key}")
                                print(f"[ERROR] This corresponds to the answer set: ")
                                print(self.clingo_output[self.clingo_hashes[clingo_key]])
                                #print("Output of nagg:")
                                #print(self.nagg_output)

                    for nagg_key in self.nagg_hashes.keys():
                        if nagg_key not in self.clingo_hashes:
                            works = False
                            if verbose:
                                print(f"[ERROR] Used Aggregate Mode: {aggregate_mode[0]} - Could not find corresponding stable model in clingo for hash {nagg_key}")
                                print(f"[ERROR] This corresponds to the answer set: ")
                                print(self.nagg_output[self.nagg_hashes[nagg_key]])
                                #print("Output of nagg:")
                                #print(self.nagg_output)


        if not works:
            if verbose:
                print("[INFO] ----------------------")
                print("[INFO] ----------------------")
                print("[INFO] ----------------------")
                print("[INFO] The answersets DIFFER!")
                print(f"[INFO] Clingo produced a total of {len(self.clingo_output)}")
                print(f"[INFO] nagg produced a total of {len(self.nagg_output)}")

            return (False, len(self.clingo_output), len(self.nagg_output))
        else: # works
            if verbose:
                print("[INFO] The answersets are the SAME!")

            return (True, len(self.clingo_output), len(self.nagg_output))
        
    
    def start_clingo(self, program_input, output, hashes, timeout=1800, mode="clingo"):

        arguments = ["clingo", "--project", "--model=0", f"--mode={mode}"]

        try:
            #p = subprocess.Popen(arguments, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=limit_virtual_memory)       
            p = subprocess.Popen(arguments, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=limit_virtual_memory)       
            (ret_vals_encoded, error_vals_encoded) = p.communicate(input=bytes(program_input, "ascii"), timeout = timeout)

            decoded_string = ret_vals_encoded.decode()

            optimization_problem = self.parse_clingo_output(decoded_string, output, hashes)

            if p.returncode != 0 and p.returncode != 10 and p.returncode != 20 and p.returncode != 30:
                print(f">>>>> Other return code than 0 in helper: {p.returncode}")

        except Exception as ex:
            try:
                p.kill()
            except Exception as e:
                pass

            print(ex)

        return optimization_problem

    def parse_clingo_output(self, output_string, output, hashes):

        next_line_model = False

        splits = output_string.split("\n")
        index = 0
        prev_line = None
        tmp_prev_line = None
        optimization_problem = None

        is_a_optimization_problem = False

        for line in splits:

            prev_line = tmp_prev_line
            tmp_prev_line = line

            if is_a_optimization_problem is False:
                if next_line_model == True:
                    splits_space = line.split(" ")
                    splits_space.sort()

                    output.append([])
                    cur_pos = len(output) - 1
                    output[cur_pos] = splits_space
                    hashes[(hash(tuple(output[cur_pos])))] = cur_pos

                    next_line_model = False

                if line.startswith("Answer"):
                    next_line_model = True

            if "Optimization" in line:
                is_a_optimization_problem = True
                hashes.clear()

            if "OPTIMUM FOUND" == line:
                optimization_problem = prev_line

            index = index + 1

        return optimization_problem

