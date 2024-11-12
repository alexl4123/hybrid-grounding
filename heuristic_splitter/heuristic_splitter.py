
import io
import os
import subprocess

from datetime import datetime

from clingo.ast import ProgramBuilder, parse_string

from heuristic_splitter.graph_creator_transformer import GraphCreatorTransformer
from heuristic_splitter.graph_data_structure import GraphDataStructure
from heuristic_splitter.graph_analyzer import GraphAnalyzer

from heuristic_splitter.heuristic_transformer import HeuristicTransformer

from heuristic_splitter.enums.heuristic_strategy import HeuristicStrategy
from heuristic_splitter.enums.treewidth_computation_strategy import TreewidthComputationStrategy
from heuristic_splitter.enums.grounding_strategy import GroundingStrategy
from heuristic_splitter.enums.sota_grounder import SotaGrounder

from heuristic_splitter.heuristic_0 import Heuristic0

from heuristic_splitter.grounding_strategy_generator import GroundingStrategyGenerator
from heuristic_splitter.grounding_strategy_handler import GroundingStrategyHandler

from heuristic_splitter.grounding_approximation.approximate_generated_sota_rules import ApproximateGeneratedSotaRules

#from heuristic_splitter.get_facts import GetFacts
#from heuristic_splitter.setup_get_facts_cython import get_facts_from_file_handle
from heuristic_splitter.get_facts_cython import get_facts_from_file_handle
from heuristic_splitter.logging_class import LoggingClass

class HeuristicSplitter:

    def __init__(self, heuristic_strategy: HeuristicStrategy, treewidth_strategy: TreewidthComputationStrategy, grounding_strategy:GroundingStrategy, 
        debug_mode, enable_lpopt,
        enable_logging = False, logging_file = None,
        output_printer = None, sota_grounder_used = SotaGrounder.GRINGO):

        self.heuristic_strategy = heuristic_strategy
        self.treewidth_strategy = treewidth_strategy
        self.grounding_strategy = grounding_strategy
        self.sota_grounder = sota_grounder_used

        self.debug_mode = debug_mode
        self.enable_lpopt = enable_lpopt
        self.output_printer = output_printer

        self.enable_logging = enable_logging
        path = None

        if self.enable_logging is True:
            from pathlib import Path
            path = Path(logging_file)

        if path is not None: 
            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, "w") as initial_overwrite:
                initial_overwrite.write("")

            self.logging_file = open(path, "a")
        else:
            self.logging_file = None
        
        if self.enable_logging:
            self.logging_class = LoggingClass(self.logging_file)
        else:
            self.logging_class = None

    def start(self, contents):

        virtual_file = io.BytesIO(contents.encode("utf-8"))

        try:
            bdg_rules = {}
            sota_rules = {}
            stratified_rules = {}
            lpopt_rules = {}

            constraint_rules = {}
            grounding_strategy = []

            graph_ds = GraphDataStructure()
            rule_dictionary = {}

            # Separate facts from other rules:
            #facts, facts_heads, other_rules, all_heads = GetFacts().get_facts_from_contents(contents)
            facts, facts_heads, other_rules, query, terms_domain = get_facts_from_file_handle(virtual_file)

            all_heads = facts_heads.copy()

            for fact_head in facts_heads.keys():
                graph_ds.add_vertex(fact_head)

            other_rules_string = "\n".join(other_rules)

            # Remove '#program' rules
            other_rules = [string_rule for string_rule in other_rules if not (string_rule.strip()).startswith("#program")]

            graph_transformer = GraphCreatorTransformer(graph_ds, rule_dictionary, other_rules, self.debug_mode)
            parse_string(other_rules_string, lambda stm: graph_transformer(stm))

            graph_analyzer = GraphAnalyzer(graph_ds)
            graph_analyzer.start()

            if self.heuristic_strategy == HeuristicStrategy.TREEWIDTH_PURE:
                heuristic = Heuristic0(self.treewidth_strategy, rule_dictionary, self.sota_grounder, self.enable_lpopt)
            else:
                raise NotImplementedError()

            heuristic_transformer = HeuristicTransformer(graph_ds, heuristic, bdg_rules,
                sota_rules, stratified_rules, lpopt_rules, constraint_rules, all_heads,
                self.debug_mode, rule_dictionary)
            parse_string(other_rules_string, lambda stm: heuristic_transformer(stm))

            if self.enable_lpopt is True and self.sota_grounder == SotaGrounder.GRINGO:
                # Check if Lpopt use is useful:
                # If so, (lpopt_used is True), then overwrite most of the other variables:

                alternative_global_number_terms=len(list(terms_domain.keys()))
                alternative_global_tuples=len(list(facts.keys()))

                # MANY ARGUMENTS:
                lpopt_used, tmp_bdg_rules, tmp_sota_rules, tmp_stratified_rules,\
                    tmp_lpopt_rules, tmp_constraint_rules, tmp_other_rules, tmp_other_rules_string,\
                    tmp_rule_dictionary, tmp_graph_ds = self.lpopt_handler(bdg_rules, sota_rules,
                        stratified_rules, lpopt_rules, constraint_rules, other_rules,
                        other_rules_string, rule_dictionary, graph_ds, facts_heads,
                        alternative_global_tuples, alternative_global_number_terms)

                if lpopt_used is True:

                    bdg_rules = tmp_bdg_rules
                    sota_rules = tmp_sota_rules
                    stratified_rules = tmp_stratified_rules
                    lpopt_rules = tmp_lpopt_rules
                    constraint_rules = tmp_constraint_rules

                    other_rules = tmp_other_rules
                    other_rules_string = tmp_other_rules_string

                    rule_dictionary = tmp_rule_dictionary
                    graph_ds = tmp_graph_ds

                else:
                    # Ground them via SOTA approaches:
                    for lpopt_rule in lpopt_rules:
                        sota_rules[lpopt_rule] = True

                    lpopt_rules.clear()

            generator_grounding_strategy = GroundingStrategyGenerator(graph_ds, bdg_rules, sota_rules,
                stratified_rules, constraint_rules, lpopt_rules, rule_dictionary)
            generator_grounding_strategy.generate_grounding_strategy(grounding_strategy)


            if self.debug_mode is True:
                print(">>>>> GROUNDING STRATEGY:")
                print(grounding_strategy)
                print("<<<<")

            if self.grounding_strategy == GroundingStrategy.FULL:

                grounding_handler = GroundingStrategyHandler(grounding_strategy, rule_dictionary, graph_ds,
                    facts,
                    query,
                    self.debug_mode, self.enable_lpopt,
                    output_printer = self.output_printer, sota_grounder = self.sota_grounder,
                    enable_logging = self.enable_logging, logging_class = self.logging_class)
                if len(grounding_strategy) > 1 or len(grounding_strategy[0]["bdg"]) > 0:
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

                if len(query.keys()) > 0:
                    print(list(query.keys())[0])

            if self.enable_logging is True:
                self.logging_class.print_to_file()
                self.logging_file.close()

        except Exception as ex:

            if self.logging_file is not None:
                self.logging_file.close()

            raise ex

    def lpopt_handler(self, bdg_rules, sota_rules, stratified_rules,
        lpopt_rules, constraint_rules, other_rules, other_rules_string,
        rule_dictionary, graph_ds, facts_heads,
        alternative_global_tuples, alternative_global_number_terms,
        ):


        # Handle LPOPT
        # 1.) Rewrite
        # 2.) Check if useful
        # 3.) If anything useful -> Re-process all other rules as before

        tmp_rule_string = ""

        lpopt_used = False

        use_lpopt_for_rules_string = ""
        do_not_use_lpopt_for_rules_string = ""

        for lpopt_rule in lpopt_rules:

            lpopt_non_rewritten_rules_string = str(rule_dictionary[lpopt_rule])
            lpopt_rewritten_rules_string = self.start_lpopt(lpopt_non_rewritten_rules_string)

            lpopt_graph_ds = GraphDataStructure()
            lpopt_rule_dictionary = {}
            graph_transformer = GraphCreatorTransformer(lpopt_graph_ds, lpopt_rule_dictionary, lpopt_rewritten_rules_string.split("\n"), self.debug_mode)
            parse_string(lpopt_rewritten_rules_string, lambda stm: graph_transformer(stm))

            approximate_non_rewritten_rules = ApproximateGeneratedSotaRules(None, rule_dictionary[lpopt_rule],
                alternative_global_number_terms=alternative_global_number_terms,
                alternative_global_tuples=alternative_global_tuples)
            approximate_non_rewritten_rule_instantiations = approximate_non_rewritten_rules.approximate_sota_size()

            approximate_rewritten_rule_instantiations = 0
            for rewritten_rule in lpopt_rule_dictionary.keys():
                tmp_approximate_non_rewritten_rules = ApproximateGeneratedSotaRules(None, lpopt_rule_dictionary[rewritten_rule],
                    alternative_global_number_terms=alternative_global_number_terms,
                    alternative_global_tuples=alternative_global_tuples)
                tmp_approximate_non_rewritten_rule_instantiations = tmp_approximate_non_rewritten_rules.approximate_sota_size()

                approximate_rewritten_rule_instantiations += tmp_approximate_non_rewritten_rule_instantiations

            if approximate_rewritten_rule_instantiations < approximate_non_rewritten_rule_instantiations:
                # Then use Lpopt rewriting
                use_lpopt_for_rules_string += lpopt_non_rewritten_rules_string + "\n"
                lpopt_used = True

            else:
                # Use rule directly:
                do_not_use_lpopt_for_rules_string += lpopt_non_rewritten_rules_string + "\n"
        
        if lpopt_used is True:
            if self.enable_logging is True:
                self.logging_class.is_lpopt_used = True
                self.logging_class.lpopt_used_for_rules = use_lpopt_for_rules_string

            # Call it once for all to-rewrite rules (to get temporary predicates correctly):
            tmp_rule_string = self.start_lpopt(use_lpopt_for_rules_string)
            tmp_rule_string += do_not_use_lpopt_for_rules_string

            tmp_graph_ds = GraphDataStructure()
            tmp_rule_dictionary = {}

            for fact_head in facts_heads.keys():
                tmp_graph_ds.add_vertex(fact_head)

            for stratified_rule in stratified_rules.keys():
                tmp_rule_string += str(rule_dictionary[stratified_rule]) + "\n"

            for sota_rule in sota_rules.keys():
                tmp_rule_string += str(rule_dictionary[sota_rule]) + "\n"

            for bdg_rule in bdg_rules.keys():
                tmp_rule_string += str(rule_dictionary[bdg_rule]) + "\n"


            tmp_rules_list = tmp_rule_string.split("\n")

            # Rmv empty lines:
            tmp_rules_list_2 = []
            for tmp_rule in tmp_rules_list:
                if len(tmp_rule) > 0: 
                    tmp_rules_list_2.append(tmp_rule)

            tmp_rules_list = tmp_rules_list_2
            tmp_rule_string = "\n".join(tmp_rules_list)

            graph_transformer = GraphCreatorTransformer(tmp_graph_ds, tmp_rule_dictionary, tmp_rules_list, self.debug_mode)
            parse_string(tmp_rule_string, lambda stm: graph_transformer(stm))

            graph_analyzer = GraphAnalyzer(tmp_graph_ds)
            graph_analyzer.start()

            if self.heuristic_strategy == HeuristicStrategy.TREEWIDTH_PURE:
                tmp_enable_lpopt = False
                heuristic = Heuristic0(self.treewidth_strategy, tmp_rule_dictionary, self.sota_grounder, tmp_enable_lpopt)
            else:
                raise NotImplementedError()

            bdg_rules = {}
            sota_rules = {}
            stratified_rules = {}
            lpopt_rules = {}

            constraint_rules = {}

            # All heads already infered, so this one is not used!
            all_heads_dev_null = {}

            heuristic_transformer = HeuristicTransformer(tmp_graph_ds, heuristic, bdg_rules,
                sota_rules, stratified_rules, lpopt_rules, constraint_rules, all_heads_dev_null,
                self.debug_mode, tmp_rule_dictionary)
            parse_string(tmp_rule_string, lambda stm: heuristic_transformer(stm))

            other_rules = tmp_rules_list
            other_rules_string = tmp_rule_string
            rule_dictionary = tmp_rule_dictionary
            graph_ds = tmp_graph_ds

        return lpopt_used, bdg_rules, sota_rules, stratified_rules, lpopt_rules, constraint_rules, other_rules, other_rules_string, rule_dictionary, graph_ds




    def start_lpopt(self, program_input, timeout=1800):

        program_string = "./lpopt.bin"

        if not os.path.isfile(program_string):
            print("[ERROR] - For treewidth aware decomposition 'lpopt.bin' is required (current directory).")
            raise Exception("lpopt.bin not found")

        seed = 11904657
        call_string = f"{program_string} -s {seed}"
        #arguments = [program_string]

        decoded_string = ""
        try:
            p = subprocess.Popen(call_string, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)       
            (ret_vals_encoded, error_vals_encoded) = p.communicate(input=bytes(program_input, "ascii"), timeout = timeout)

            decoded_string = ret_vals_encoded.decode()
            error_vals_decoded = error_vals_encoded.decode()

            if p.returncode != 0:
                print(f">>>>> Other return code than 0 in helper: {p.returncode}")
                print(decoded_string)
                print(error_vals_decoded)
                raise Exception(error_vals_decoded)

        except Exception as ex:
            try:
                p.kill()
            except Exception as e:
                pass

            print(ex)

            raise NotImplementedError() # TBD: Continue if possible

        return decoded_string

