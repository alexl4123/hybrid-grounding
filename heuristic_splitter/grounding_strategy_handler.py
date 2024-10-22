
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


class CustomOutputPrinter(DefaultOutputPrinter):

    def __init__(self):
        self.string = ""

    def custom_print(self, string):
        print(string)
        #self.string = self.string + str(string) + '\n'
        pass

    def get_string(self):
        return self.string

class GroundingStrategyHandler:

    def __init__(self, grounding_strategy: GroundingStrategyGenerator, rule_dictionary, graph_ds: GraphDataStructure, debug_mode):

        self.grounding_strategy = grounding_strategy
        self.rule_dictionary = rule_dictionary
        self.graph_ds = graph_ds
        self.debug_mode = debug_mode

    def ground(self):

        grounded_program = ""
        domain_transformer = DomainTransformer()

        for level_index in range(len(self.grounding_strategy)):

            level = self.grounding_strategy[level_index]
            sota_rules = level["sota"]
            bdg_rules = level["bdg"]
            lpopt_rules = level["lpopt"]

            if self.debug_mode is True:
                print(f"-- {level_index}: SOTA-RULES: {sota_rules}, BDG-RULES: {bdg_rules}")

            if len(bdg_rules) > 0:

                domain_transformer.update_domain_sizes()
                tmp_bdg_old_found_rules = []
                tmp_bdg_new_found_rules = []

                for bdg_rule in bdg_rules:

                    rule = self.rule_dictionary[bdg_rule]

                    str_rule = str(rule)

                    approximate_sota_rules_transformer = ApproximateGeneratedSotaRulesTransformer(domain_transformer)
                    parse_string(str_rule, lambda stm: approximate_sota_rules_transformer(stm))

                    approximated_sota_rule_instantiations = approximate_sota_rules_transformer.rule_tuples
 

                    variable_domains_transformer = VariableDomainInferenceTransformer(domain_transformer, rule)
                    parse_string(str_rule, lambda stm: variable_domains_transformer(stm))

                    variable_domains = variable_domains_transformer.variable_domains
                    head_variables = variable_domains_transformer.head_variables

                    approximate_bdg_rules_transformer = ApproximateGeneratedBDGRulesTransformer(domain_transformer, variable_domains, rule, head_variables, self.graph_ds, self.rule_dictionary)
                    parse_string(str_rule, lambda stm: approximate_bdg_rules_transformer(stm))

                    approximated_bdg_old_rule_instantiations = approximate_bdg_rules_transformer.bdg_rules_old
                    approximated_bdg_new_rule_instantiations = approximate_bdg_rules_transformer.bdg_rules_new
 

                    used_method = None
                    if approximated_sota_rule_instantiations < approximated_bdg_new_rule_instantiations and approximated_sota_rule_instantiations < approximated_bdg_old_rule_instantiations:
                        used_method = "SOTA"
                    elif approximated_bdg_old_rule_instantiations < approximated_sota_rule_instantiations and approximated_bdg_old_rule_instantiations < approximated_bdg_new_rule_instantiations:
                        used_method = "BDG_OLD"
                    elif approximated_bdg_new_rule_instantiations < approximated_sota_rule_instantiations and approximated_bdg_new_rule_instantiations < approximated_bdg_old_rule_instantiations and rule.is_tight is True:
                        used_method = "BDG_NEW"
                    elif approximated_sota_rule_instantiations < approximated_bdg_old_rule_instantiations:
                        used_method = "SOTA"
                    else:
                        used_method = "BDG_OLD"

                    # TODO - RMV STATEMENT!
                    # used_method = "BDG_NEW"

                    if self.debug_mode is True:
                        print("-------------------------")
                        print(f"Rule: {rule}")
                        print(f"SOTA: {approximated_sota_rule_instantiations}")
                        print(f"BDG-OLD: {approximated_bdg_old_rule_instantiations}")
                        print(f"BDG-NEW: {approximated_bdg_new_rule_instantiations}")
                        print(f"USED-METHOD: {used_method}")
                        print("-------------------------")

                    if used_method == "SOTA":
                        sota_rules.append(bdg_rule)
                    elif used_method == "BDG_OLD":
                        tmp_bdg_old_found_rules.append(bdg_rule)
                    else:
                        tmp_bdg_new_found_rules.append(bdg_rule) 

                if True:
                    no_show = False
                    ground_guess = True
                    # Custom printer keeps result of prototype (NaGG)
                    aggregate_mode = AggregateMode.RA
                    cyclic_strategy = CyclicStrategy.LEVEL_MAPPING
                    grounding_mode = GroundingModes.REWRITE_AGGREGATES_GROUND_FULLY

                    if len(tmp_bdg_new_found_rules) > 0:

                        tmp_rules_string = self.rule_list_to_rule_string(tmp_bdg_new_found_rules)

                        nagg_domain_connector_transformer = NaGGDomainConnectorTransformer()
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

                        nagg_domain_connector_transformer = NaGGDomainConnectorTransformer()
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
                decoded_string = self.start_gringo(grounded_program, sota_rules)

                parse_string(decoded_string, lambda stm: domain_transformer(stm))


                grounded_program = decoded_string

                if self.debug_mode is True:
                    print("+++++")
                    print(sota_rules)
                    print(decoded_string)
                    print(domain_transformer.domain_dictionary)


        if self.debug_mode is True:
            print("--- FINAL ---") 
        print(grounded_program)

    def rule_list_to_rule_string(self, rules):
        program_input = "\n"
        for rule in rules:
            if rule in self.rule_dictionary:
                program_input += f"{str(self.rule_dictionary[rule])}\n"
            else:
                print(f"[ERROR] - Could not find rule {rule} in rule-dictionary.")
                raise NotImplementedError() # TBD Fallback

        return program_input


    def start_gringo(self, grounded_program, rules, timeout=1800):

        program_input = grounded_program + "\n" + self.rule_list_to_rule_string(rules) 

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

