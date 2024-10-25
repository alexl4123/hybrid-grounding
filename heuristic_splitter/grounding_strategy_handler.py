
import os
import subprocess

from clingo.ast import ProgramBuilder, parse_string

from heuristic_splitter.graph_data_structure import GraphDataStructure

from heuristic_splitter.grounding_strategy_generator import GroundingStrategyGenerator
from heuristic_splitter.domain_transformer import DomainTransformer

from heuristic_splitter.grounding_approximation.approximate_generated_sota_rules_transformer import ApproximateGeneratedSotaRulesTransformer
from heuristic_splitter.grounding_approximation.approximate_generated_bdg_rules_transformer import ApproximateGeneratedBDGRulesTransformer
from heuristic_splitter.grounding_approximation.variable_domain_inference_transformer import VariableDomainInferenceTransformer

from heuristic_splitter.nagg_domain_connector_transformer import NaGGDomainConnectorTransformer
from heuristic_splitter.nagg_domain_connector import NaGGDomainConnector

from nagg.nagg import NaGG
from nagg.default_output_printer import DefaultOutputPrinter
from nagg.aggregate_strategies.aggregate_mode import AggregateMode
from nagg.cyclic_strategy import CyclicStrategy
from nagg.grounding_modes import GroundingModes
from nagg.foundedness_strategy import FoundednessStrategy
from heuristic_splitter.domain_inferer import DomainInferer

class CustomOutputPrinter(DefaultOutputPrinter):

    def __init__(self):
        self.strings = []

    def custom_print(self, string):
        #print(string)
        self.strings.append(string)

    def get_string(self):
        return "\n".join(self.strings)

class GroundingStrategyHandler:

    def __init__(self, grounding_strategy: GroundingStrategyGenerator, rule_dictionary, graph_ds: GraphDataStructure, facts, debug_mode, enable_lpopt):

        self.grounding_strategy = grounding_strategy
        self.rule_dictionary = rule_dictionary
        self.facts = facts
        
        self.graph_ds = graph_ds

        self.debug_mode = debug_mode
        self.enable_lpopt = enable_lpopt

    def ground(self):

        grounded_program = "\n".join(list(self.facts.keys()))
        #domain_transformer = DomainTransformer()
        domain_transformer = DomainInferer()

        for level_index in range(len(self.grounding_strategy)):

            if domain_transformer.unsat_prg_found is True:
                break

            level = self.grounding_strategy[level_index]
            sota_rules = level["sota"]
            bdg_rules = level["bdg"]

            if self.debug_mode is True:
                print(f"-- {level_index}: SOTA-RULES: {sota_rules}, BDG-RULES: {bdg_rules}")

            if len(bdg_rules) > 0:

                domain_transformer.update_domain_sizes()
                tmp_bdg_old_found_rules = []
                tmp_bdg_new_found_rules = []

                for bdg_rule in bdg_rules:

                    rule = self.rule_dictionary[bdg_rule]

                    approx_number_rules, used_method, rule_str = self.get_best_method_by_approximated_rule_count(domain_transformer, rule)

                    if self.enable_lpopt is True:
                        self.lpopt_case(rule, domain_transformer, approx_number_rules, sota_rules, tmp_bdg_old_found_rules, tmp_bdg_new_found_rules, used_method, bdg_rule)
                    else:
                        if used_method == "SOTA":
                            sota_rules.append(bdg_rule)
                        elif used_method == "BDG_OLD":
                            tmp_bdg_old_found_rules.append(bdg_rule)
                        else:
                            tmp_bdg_new_found_rules.append(bdg_rule) 

                no_show = False
                ground_guess = True
                # Custom printer keeps result of prototype (NaGG)
                aggregate_mode = AggregateMode.RA
                cyclic_strategy = CyclicStrategy.LEVEL_MAPPING
                grounding_mode = GroundingModes.REWRITE_AGGREGATES_GROUND_FULLY

                if len(tmp_bdg_new_found_rules) > 0:

                    tmp_rules_string = self.rule_list_to_rule_string(tmp_bdg_new_found_rules)

                    nagg_domain_connector_transformer = NaGGDomainConnectorTransformer(domain_transformer)
                    parse_string(tmp_rules_string, lambda stm: nagg_domain_connector_transformer(stm))

                    nagg_domain_connector = NaGGDomainConnector(
                        domain_transformer.domain_dictionary, domain_transformer.total_domain,
                        nagg_domain_connector_transformer.nagg_safe_variables,
                        nagg_domain_connector_transformer.shown_predicates)
                    nagg_domain_connector.convert_data_structures()
                
                    custom_printer = CustomOutputPrinter()
                    #program_input = grounded_program + "\n#program rules.\n" + tmp_rules_string
                    program_input = "\n#program rules.\n" + tmp_rules_string

                    foundedness_strategy = FoundednessStrategy.SATURATION

                    nagg = NaGG(no_show = no_show, ground_guess = ground_guess, output_printer = custom_printer,
                        aggregate_mode = aggregate_mode, cyclic_strategy=cyclic_strategy,
                        grounding_mode=grounding_mode, foundedness_strategy=foundedness_strategy)
                    nagg.start(program_input, nagg_domain_connector)

                    #grounded_program = custom_printer.get_string()
                    grounded_program = grounded_program + custom_printer.get_string()
                    
                if len(tmp_bdg_old_found_rules) > 0:

                    tmp_rules_string = self.rule_list_to_rule_string(tmp_bdg_old_found_rules)

                    nagg_domain_connector_transformer = NaGGDomainConnectorTransformer(domain_transformer)
                    parse_string(tmp_rules_string, lambda stm: nagg_domain_connector_transformer(stm))

                    nagg_domain_connector = NaGGDomainConnector(
                        domain_transformer.domain_dictionary, domain_transformer.total_domain,
                        nagg_domain_connector_transformer.nagg_safe_variables,
                        nagg_domain_connector_transformer.shown_predicates)
                    nagg_domain_connector.convert_data_structures()
                
                    custom_printer = CustomOutputPrinter()
                    program_input = "\n#program rules.\n" + tmp_rules_string

                    foundedness_strategy = FoundednessStrategy.DEFAULT

                    nagg = NaGG(no_show = no_show, ground_guess = ground_guess, output_printer = custom_printer,
                        aggregate_mode = aggregate_mode, cyclic_strategy=cyclic_strategy,
                        grounding_mode=grounding_mode, foundedness_strategy=foundedness_strategy)
                    nagg.start(program_input, nagg_domain_connector)

                    grounded_program = grounded_program + custom_printer.get_string()

            if len(sota_rules) > 0:
                # Ground SOTA rules with SOTA (gringo/IDLV):
                sota_rules_string = self.rule_list_to_rule_string(sota_rules) 
                program_input = grounded_program + "\n" + sota_rules_string
                decoded_string = self.start_gringo(program_input)

                #parse_string(decoded_string, lambda stm: domain_transformer(stm))
                domain_transformer.infer_domain(decoded_string)

                grounded_program = decoded_string

                if self.debug_mode is True:
                    print("+++++")
                    print(sota_rules)
                    print(sota_rules_string)
                    print("++")
                    print(decoded_string)
                    print(domain_transformer.domain_dictionary)


        if self.debug_mode is True:
            print("--- FINAL ---") 
        print(grounded_program)

    def add_approximate_generated_ground_rules_for_non_ground_rule(self, domain_transformer, rule, str_rule, methods_approximations):
        """
        Calls those methods that approximate the number of instantiated rules.
        """

        approximate_sota_rules_transformer = ApproximateGeneratedSotaRulesTransformer(domain_transformer)
        parse_string(str_rule, lambda stm: approximate_sota_rules_transformer(stm))
        
        approximated_sota_rule_instantiations = approximate_sota_rules_transformer.rule_tuples
        methods_approximations.append((approximated_sota_rule_instantiations, "SOTA", str_rule))
        
        variable_domains_transformer = VariableDomainInferenceTransformer(domain_transformer)
        parse_string(str_rule, lambda stm: variable_domains_transformer(stm))
        
        variable_domains = variable_domains_transformer.variable_domains
        head_variables = variable_domains_transformer.head_variables
        
        approximate_bdg_rules_transformer = ApproximateGeneratedBDGRulesTransformer(domain_transformer, variable_domains, rule, head_variables, self.graph_ds, self.rule_dictionary)
        parse_string(str_rule, lambda stm: approximate_bdg_rules_transformer(stm))
        
        approximated_bdg_old_rule_instantiations = approximate_bdg_rules_transformer.bdg_rules_old
        approximated_bdg_new_rule_instantiations = approximate_bdg_rules_transformer.bdg_rules_new

        methods_approximations.append((approximated_bdg_old_rule_instantiations, "BDG_OLD", str_rule))
        methods_approximations.append((approximated_bdg_new_rule_instantiations, "BDG_NEW", str_rule))

        if self.debug_mode is True:
            print("-------------------------")
            print(f"Rule: {str_rule}")
            print(f"SOTA: {approximated_sota_rule_instantiations}")
            print(f"BDG-OLD: {approximated_bdg_old_rule_instantiations}")
            print(f"BDG-NEW: {approximated_bdg_new_rule_instantiations}")
            print("-------------------------")


    def get_best_method_by_approximated_rule_count(self, domain_transformer, rule, str_rule = None):
        """
        Calls approximate instantiated rules helper, and determines best to use grounding method accordingly.
        """

        methods_approximations = []
        if str_rule is None:
            str_rule = str(rule)

        self.add_approximate_generated_ground_rules_for_non_ground_rule(domain_transformer,
            rule, str_rule, methods_approximations)
        
        min_element = min(methods_approximations, key=lambda x: x[0])

        approx_number_rules = min_element[0]
        used_method = min_element[1]
        rule_str = min_element[2]

        return approx_number_rules, used_method, rule_str

    def lpopt_case(self, rule, domain_transformer, approx_number_rules, sota_rules, tmp_bdg_old_found_rules, tmp_bdg_new_found_rules, used_method, bdg_rule):
        """
        If grounding should be done with a treewidth-aware case, then lpopt will be called to decompose the rules.
        If it is expected that lpopt will perform better, then use the rewritten rules, otw. the methods without rewriting.
        """

        rewritten_rules = self.start_lpopt(str(rule))
        
        if self.debug_mode is True:
            print("---> lpopt output:")
            print(rewritten_rules)
        
        approx_number_rules_tw_total = 0
        
        lpopt_rules = []
        
        for rewritten_rule in rewritten_rules.split("\n"):
        
            if len(rewritten_rule.strip()) == 0:
                continue
        
        
            approx_number_rules_rw, used_method_rw, rule_str_rw = self.get_best_method_by_approximated_rule_count(domain_transformer, rule, rewritten_rule)
        
            approx_number_rules_tw_total += approx_number_rules_rw
            lpopt_rules.append((used_method_rw, rule_str_rw))
        
            if self.debug_mode is True:
                print(f"-----> Lpopt rule '{rewritten_rule}' would generate rules: {approx_number_rules_rw}")
        
        if self.debug_mode is True:
            print(f"-----> Total lpopt generated rules: {approx_number_rules_tw_total}")
        
        if approx_number_rules_tw_total < approx_number_rules:
            # Using lpopt is better
        
            for used_method_tmp, rule_str_tmp in lpopt_rules:
        
                if used_method_tmp == "SOTA":
                    sota_rules.append(rule_str_tmp)
                elif used_method_tmp == "BDG_OLD":
                    tmp_bdg_old_found_rules.append(rule_str_tmp)
                else:
                    tmp_bdg_new_found_rules.append(rule_str_tmp) 
        else:
            if used_method == "SOTA":
                sota_rules.append(bdg_rule)
            elif used_method == "BDG_OLD":
                tmp_bdg_old_found_rules.append(bdg_rule)
            else:
                tmp_bdg_new_found_rules.append(bdg_rule) 



    def rule_list_to_rule_string(self, rules):
        program_input = "\n"
        for rule in rules:
            if rule in self.rule_dictionary:
                program_input += f"{str(self.rule_dictionary[rule])}\n"
            elif isinstance(rule, str):
                program_input += rule
            else:
                print(f"[ERROR] - Could not find rule {rule} in rule-dictionary.")
                raise NotImplementedError() # TBD Fallback

        return program_input


    def start_gringo(self, program_input, timeout=1800):

        arguments = ["gringo", "-t"]

        decoded_string = ""
        try:
            p = subprocess.Popen(arguments, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)       
            (ret_vals_encoded, error_vals_encoded) = p.communicate(input=bytes(program_input, "ascii"), timeout = timeout)

            decoded_string = ret_vals_encoded.decode()
            error_vals_decoded = error_vals_encoded.decode()

            if p.returncode != 0 and p.returncode != 10 and p.returncode != 20 and p.returncode != 30:
                print(f">>>>> Other return code than 0 in helper: {p.returncode}")
                print(error_vals_decoded)

        except Exception as ex:
            try:
                p.kill()
            except Exception as e:
                pass

            print(ex)

            raise NotImplementedError() # TBD: Continue if possible

        return decoded_string


    def start_lpopt(self, program_input, timeout=1800):

        program_string = "./lpopt.bin"

        if not os.path.isfile(program_string):
            print("[ERROR] - For treewidth aware decomposition 'lpopt.bin' is required (current directory).")
            raise Exception("lpopt.bin not found")

        arguments = [program_string]
        print(program_input)

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

