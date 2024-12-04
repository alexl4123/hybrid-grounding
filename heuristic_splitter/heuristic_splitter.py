
import io
import os
import subprocess
import gc


#from memory_profiler import profile

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
from heuristic_splitter.enums.output import Output

from heuristic_splitter.heuristic_0 import Heuristic0

from heuristic_splitter.grounding_strategy_generator import GroundingStrategyGenerator
from heuristic_splitter.grounding_strategy_handler import GroundingStrategyHandler, CustomOutputPrinter

from heuristic_splitter.grounding_approximation.approximate_generated_sota_rules import ApproximateGeneratedSotaRules

from heuristic_splitter.program_structures.program_ds import ProgramDS

from clingo.application import clingo_main
from heuristic_splitter.cdnl.starter import Starter
from heuristic_splitter.cdnl.cdnl_data_structure import CDNLDataStructure
from heuristic_splitter.cdnl.positive_cycle_transformer import PositiveCycleTransformer

#from heuristic_splitter.get_facts import GetFacts
#from heuristic_splitter.setup_get_facts_cython import get_facts_from_file_handle

from heuristic_splitter.get_facts_cython import get_facts_from_file_handle
from heuristic_splitter.logging_class import LoggingClass

class HeuristicSplitter:

    def __init__(self, heuristic_strategy: HeuristicStrategy, treewidth_strategy: TreewidthComputationStrategy, grounding_strategy:GroundingStrategy, 
        debug_mode, enable_lpopt,
        enable_logging = False, logging_file = None,
        output_printer = None, sota_grounder_used = SotaGrounder.GRINGO,
        output_type = Output.DEFAULT_GROUNDER):

        self.heuristic_strategy = heuristic_strategy
        self.treewidth_strategy = treewidth_strategy
        self.grounding_strategy = grounding_strategy
        self.sota_grounder = sota_grounder_used

        self.debug_mode = debug_mode
        self.enable_lpopt = enable_lpopt

        # TODO
        self.ground_and_solve = True

        if self.ground_and_solve is True:
            self.output_printer = CustomOutputPrinter()
        else:
            self.output_printer = None

        self.output_type = output_type

        self.enable_logging = enable_logging

        self.cdnl_data_structure = CDNLDataStructure()

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

        self.program_ds = ProgramDS()

    #@profile
    def start(self, contents):

        virtual_file = io.BytesIO(contents.encode("utf-8"))

        # Explicitly invoke garbage collection (I do not need facts anymore) 
        del contents
        gc.collect()

        try:
            bdg_rules = {}
            sota_rules = {}
            stratified_rules = {}
            lpopt_rules = {}

            constraint_rules = {}
            grounding_strategy = []

            graph_ds = GraphDataStructure()
            rule_dictionary = {}

            self.cdnl_data_structure.graph_ds = graph_ds
            self.cdnl_data_structure.rule_dictionary = rule_dictionary

            # Separate facts from other rules:
            facts, facts_heads, other_rules, query, terms_domain = get_facts_from_file_handle(virtual_file)

            # Explicitly invoke garbage collection (I do not need facts anymore) 
            del virtual_file
            gc.collect()

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
                self.debug_mode, rule_dictionary, self.program_ds)
            parse_string(other_rules_string, lambda stm: heuristic_transformer(stm))

            if self.enable_lpopt is True and self.sota_grounder == SotaGrounder.GRINGO and len(list(facts_heads.values())) > 0:
                # Check if Lpopt use is useful:
                # If so, (lpopt_used is True), then overwrite most of the other variables:

                alternative_global_number_terms=len(list(terms_domain.keys()))
                alternative_global_tuples=len(list(facts.keys()))

                max_arity_in_facts = max(facts_heads.values())
                #number_facts_heads = len(list(facts_heads.keys()))
                #alternative_adjusted_tuples = alternative_global_tuples / number_facts_heads
                if max_arity_in_facts > 0:
                    alternative_adjusted_tuples = alternative_global_tuples**(1/max_arity_in_facts)
                else:
                    alternative_adjusted_tuples = alternative_global_tuples

                # MANY ARGUMENTS/CALL LPOPT:
                lpopt_used, tmp_bdg_rules, tmp_sota_rules, tmp_stratified_rules,\
                    tmp_lpopt_rules, tmp_constraint_rules, tmp_other_rules, tmp_other_rules_string,\
                    tmp_rule_dictionary, tmp_graph_ds = self.lpopt_handler(bdg_rules, sota_rules,
                        stratified_rules, lpopt_rules, constraint_rules, other_rules,
                        other_rules_string, rule_dictionary, graph_ds, facts_heads,
                        alternative_global_tuples, alternative_global_number_terms,
                        alternative_adjusted_tuples)

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


            if self.ground_and_solve is True:
                # Go through all SCCs
                # See if there is any non-trivial, where BDG might be used
                # If so --> Apply rewritings!


                new_rules = []
                new_bdg_rules = []

                rewritten_data_structure = {}

                scc_index = 0
                for scc in graph_ds.positive_sccs:

                    is_bdg_cycle = False

                    for node in list(scc):
                        rules = graph_ds.node_to_rule_lookup[node]

                        for rule in rules:
                            if rule in bdg_rules:
                                is_bdg_cycle = True
                                break

                        if is_bdg_cycle is True:
                            break
                    
                    if is_bdg_cycle is True:
                        # rewrite rules:
                        for node in list(scc):
                            rules = graph_ds.node_to_rule_lookup[node]

                            rules_string_array = []
                            bdg_rules_string_array = []

                            for rule in rules:
                                if rule in bdg_rules:
                                    bdg_rules_string_array.append(str(rule_dictionary[rule]))
                                else:
                                    rules_string_array.append(str(rule_dictionary[rule]))

                            # Non-BDG Rules:
                            rules_string = "\n".join(rules_string_array) 
                            positive_cycle_transformer = PositiveCycleTransformer(scc_index, function_visit_index=0)
                            parse_string(rules_string, lambda stm: positive_cycle_transformer(stm))

                            new_rules += positive_cycle_transformer.transformed_rules
                            new_rules += positive_cycle_transformer.new_rules
                            rewritten_data_structure = rewritten_data_structure | positive_cycle_transformer.rewritten_to_original_dict

                            prev_function_visit_index = positive_cycle_transformer.function_visit_index

                            # Same for BDG:
                            rules_string = "\n".join(bdg_rules_string_array) 
                            positive_cycle_transformer = PositiveCycleTransformer(scc_index, function_visit_index=prev_function_visit_index)
                            parse_string(rules_string, lambda stm: positive_cycle_transformer(stm))

                            new_bdg_rules += positive_cycle_transformer.transformed_rules
                            new_rules += positive_cycle_transformer.new_rules
                            rewritten_data_structure = rewritten_data_structure | positive_cycle_transformer.rewritten_to_original_dict

                    else:
                        for node in list(scc):
                            rules = graph_ds.node_to_rule_lookup[node]

                            rules_string_array = []
                            bdg_rules_string_array = []
                            for rule in rules:
                                if rule in bdg_rules:
                                    bdg_rules_string_array.append(str(rule_dictionary[rule]))
                                else:
                                    rules_string_array.append(str(rule_dictionary[rule]))

                            new_rules += rules_string_array
                            new_bdg_rules += bdg_rules_string_array
                    scc_index += 1

                self.cdnl_data_structure.rewritten_to_original_dict = rewritten_data_structure

                all_new_rules = new_rules + ["#program rules."] + new_bdg_rules
            
                tmp_graph_ds = GraphDataStructure()
                tmp_rule_dictionary = {}

                self.cdnl_data_structure.graph_ds = tmp_graph_ds
                self.cdnl_data_structure.rule_dictionary = tmp_rule_dictionary

                program_ds_tmp = ProgramDS()

                for fact_head in facts_heads.keys():
                    tmp_graph_ds.add_vertex(fact_head)

                all_new_rules_string = "\n".join(all_new_rules)
                graph_transformer = GraphCreatorTransformer(tmp_graph_ds, tmp_rule_dictionary, all_new_rules, self.debug_mode)
                parse_string(all_new_rules_string, lambda stm: graph_transformer(stm))

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
                    self.debug_mode, tmp_rule_dictionary, program_ds_tmp)
                parse_string(all_new_rules_string, lambda stm: heuristic_transformer(stm))

                other_rules = all_new_rules
                other_rules_string = all_new_rules_string
                rule_dictionary = tmp_rule_dictionary
                graph_ds = tmp_graph_ds
                self.program_ds = program_ds_tmp



            generator_grounding_strategy = GroundingStrategyGenerator(graph_ds, bdg_rules, sota_rules,
                stratified_rules, constraint_rules, lpopt_rules, rule_dictionary, self.program_ds)
            generator_grounding_strategy.generate_grounding_strategy(grounding_strategy)


            if self.debug_mode is True:
                print(">>>>> GROUNDING STRATEGY:")
                print(grounding_strategy)
                print("<<<<")

            if self.grounding_strategy == GroundingStrategy.FULL:

                grounding_handler = GroundingStrategyHandler(grounding_strategy, rule_dictionary, graph_ds,
                    facts, query,
                    self.debug_mode, self.enable_lpopt,
                    output_printer = self.output_printer, sota_grounder = self.sota_grounder,
                    enable_logging = self.enable_logging, logging_class = self.logging_class,
                    output_type = self.output_type, cdnl_data_structure=self.cdnl_data_structure,
                    ground_and_solve=self.ground_and_solve)
                if len(grounding_strategy) > 1 or len(grounding_strategy[0]["bdg"]) > 0:
                    if self.enable_logging is True:
                        self.logging_class.is_single_ground_call = False

                    domain_transformer = grounding_handler.ground()
                    grounding_handler.output_grounded_program(all_heads, domain_transformer)
                else:
                    if self.enable_logging is True:
                        self.logging_class.is_single_ground_call = True

                    grounding_handler.single_ground_call(all_heads)


                if self.ground_and_solve is True:
                    if self.output_printer is not None:
                        clingo_main(
                            Starter(self.output_printer.get_string(), self.cdnl_data_structure)
                            )


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
        alternative_adjusted_tuples,
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

            if rule_dictionary[lpopt_rule].in_lpopt_rules is False:
                approximate_non_rewritten_rules = ApproximateGeneratedSotaRules(None, rule_dictionary[lpopt_rule],
                    alternative_global_number_terms=alternative_global_number_terms,
                    alternative_adjusted_tuples_per_arity=alternative_adjusted_tuples)
                approximate_non_rewritten_rule_instantiations = approximate_non_rewritten_rules.approximate_sota_size()

                approximate_rewritten_rule_instantiations = 0
                for rewritten_rule in lpopt_rule_dictionary.keys():
                    tmp_approximate_non_rewritten_rules = ApproximateGeneratedSotaRules(None, lpopt_rule_dictionary[rewritten_rule],
                        alternative_global_number_terms=alternative_global_number_terms,
                        alternative_adjusted_tuples_per_arity=alternative_adjusted_tuples)
                    tmp_approximate_non_rewritten_rule_instantiations = tmp_approximate_non_rewritten_rules.approximate_sota_size()

                    approximate_rewritten_rule_instantiations += tmp_approximate_non_rewritten_rule_instantiations
            else: # in_lpopt_rules is True (so use lpopt anyway):
                # USE LPOPT if in #program lpopt.
                approximate_rewritten_rule_instantiations = -1
                approximate_non_rewritten_rule_instantiations = 0

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

            self.cdnl_data_structure.graph_ds = tmp_graph_ds
            self.cdnl_data_structure.rule_dictionary = tmp_rule_dictionary

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
            
            program_ds_tmp = ProgramDS()

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
                self.debug_mode, tmp_rule_dictionary, program_ds_tmp)
            parse_string(tmp_rule_string, lambda stm: heuristic_transformer(stm))

            other_rules = tmp_rules_list
            other_rules_string = tmp_rule_string
            rule_dictionary = tmp_rule_dictionary
            graph_ds = tmp_graph_ds
            self.program_ds = program_ds_tmp

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

