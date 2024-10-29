
import io
import os
import subprocess

from datetime import datetime
from pathlib import Path

from clingo.ast import ProgramBuilder, parse_string

from heuristic_splitter.graph_creator_transformer import GraphCreatorTransformer
from heuristic_splitter.graph_data_structure import GraphDataStructure
from heuristic_splitter.graph_analyzer import GraphAnalyzer

from heuristic_splitter.heuristic_transformer import HeuristicTransformer

from heuristic_splitter.heuristic_strategy import HeuristicStrategy
from heuristic_splitter.treewidth_computation_strategy import TreewidthComputationStrategy
from heuristic_splitter.grounding_strategy import GroundingStrategy

from heuristic_splitter.heuristic_0 import Heuristic0

from heuristic_splitter.grounding_strategy_generator import GroundingStrategyGenerator
from heuristic_splitter.grounding_strategy_handler import GroundingStrategyHandler

#from heuristic_splitter.get_facts import GetFacts
#from heuristic_splitter.setup_get_facts_cython import get_facts_from_file_handle
from heuristic_splitter.get_facts_cython import get_facts_from_file_handle

class HeuristicSplitter:

    def __init__(self, heuristic_strategy: HeuristicStrategy, treewidth_strategy: TreewidthComputationStrategy, grounding_strategy:GroundingStrategy, 
        debug_mode, enable_lpopt,
        enable_logging = False, logging_file = None,
        output_printer = None,):

        self.heuristic_strategy = heuristic_strategy
        self.treewidth_strategy = treewidth_strategy
        self.grounding_strategy = grounding_strategy
        self.debug_mode = debug_mode
        self.enable_lpopt = enable_lpopt
        self.output_printer = output_printer

        self.enable_logging = enable_logging
        path = None
        if self.enable_logging is True and logging_file is None:
            # Set default logging file:
            current_datetime = datetime.now()
            path_list = ["logs", current_datetime.strftime("%Y%m%d-%H%M%S") + ".log"]
            path = Path(*path_list)
        elif self.enable_logging is True:
            path = Path(logging_file)

        if path is not None: 
            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, "w") as initial_overwrite:
                initial_overwrite.write("")

            self.logging_file = open(path, "a")
        else:
            self.logging_file = None

    def start(self, contents):

        virtual_file = io.BytesIO(contents.encode("utf-8"))

        try:
            bdg_rules = {}
            sota_rules = {}
            stratified_rules = {}
            constraint_rules = {}
            grounding_strategy = []
            graph_ds = GraphDataStructure()
            rule_dictionary = {}

            # Separate facts from other rules:
            #facts, facts_heads, other_rules, all_heads = GetFacts().get_facts_from_contents(contents)
            facts, facts_heads, other_rules = get_facts_from_file_handle(virtual_file)

            all_heads = facts_heads.copy()

            for fact_head in facts_heads.keys():
                graph_ds.add_vertex(fact_head)

            other_rules_string = "\n".join(other_rules)

            if self.enable_lpopt is True:
                other_rules_string = self.start_lpopt(other_rules_string)

            graph_transformer = GraphCreatorTransformer(graph_ds, rule_dictionary, other_rules)
            parse_string(other_rules_string, lambda stm: graph_transformer(stm))
            
            graph_analyzer = GraphAnalyzer(graph_ds)
            graph_analyzer.start()

            if self.heuristic_strategy == HeuristicStrategy.TREEWIDTH_PURE:
                heuristic = Heuristic0(self.treewidth_strategy, rule_dictionary)
            else:
                raise NotImplementedError()

            heuristic_transformer = HeuristicTransformer(graph_ds, heuristic, bdg_rules, sota_rules, stratified_rules, constraint_rules, all_heads)
            parse_string(other_rules_string, lambda stm: heuristic_transformer(stm))

            generator_grounding_strategy = GroundingStrategyGenerator(graph_ds, bdg_rules, sota_rules,
                stratified_rules, constraint_rules, rule_dictionary)
            generator_grounding_strategy.generate_grounding_strategy(grounding_strategy)


            if self.debug_mode is True:
                print(">>>>> GROUNDING STRATEGY:")
                print(grounding_strategy)
                print("<<<<")

            if self.grounding_strategy == GroundingStrategy.FULL:

                grounding_handler = GroundingStrategyHandler(grounding_strategy, rule_dictionary, graph_ds,
                    facts,
                    self.debug_mode, self.enable_lpopt,
                    output_printer = self.output_printer,
                    enable_logging = self.enable_logging, logging_file = self.logging_file,)
                if len(grounding_strategy) > 1:
                    grounding_handler.ground()
                    grounding_handler.output_grounded_program(all_heads)
                else:
                    grounding_handler.single_ground_call(all_heads)

            else:

                facts_string = "\n".join(list(facts.keys()))
                print(facts_string)

                for sota_rule in sota_rules.keys():
                    print(str(rule_dictionary[sota_rule]))

                for strat_rule in stratified_rules.keys():
                    print(str(rule_dictionary[strat_rule]))

                if len(list(bdg_rules.keys())) > 0:
                    print("#program rules.")

                    for bdg_rule in bdg_rules.keys():
                        print(str(rule_dictionary[bdg_rule]))

            if self.logging_file is not None:
                self.logging_file.close()

        except Exception as ex:

            if self.logging_file is not None:
                self.logging_file.close()

            raise ex

    def start_lpopt(self, program_input, timeout=1800):

        program_string = "./lpopt.bin"

        if not os.path.isfile(program_string):
            print("[ERROR] - For treewidth aware decomposition 'lpopt.bin' is required (current directory).")
            raise Exception("lpopt.bin not found")

        arguments = [program_string]

        decoded_string = ""
        try:
            p = subprocess.Popen(arguments, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)       
            (ret_vals_encoded, error_vals_encoded) = p.communicate(input=bytes(program_input, "ascii"), timeout = timeout)

            decoded_string = ret_vals_encoded.decode()
            error_vals_decoded = error_vals_encoded.decode()

            if p.returncode != 0:
                print(f">>>>> Other return code than 0 in helper: {p.returncode}")
                raise Exception(error_vals_decoded)

        except Exception as ex:
            try:
                p.kill()
            except Exception as e:
                pass

            print(ex)

            raise NotImplementedError() # TBD: Continue if possible

        return decoded_string

