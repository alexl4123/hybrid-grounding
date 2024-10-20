
import subprocess

from clingo.ast import ProgramBuilder, parse_string

from heuristic_splitter.graph_data_structure import GraphDataStructure

from heuristic_splitter.grounding_strategy_generator import GroundingStrategyGenerator
from heuristic_splitter.domain_transformer import DomainTransformer

from heuristic_splitter.grounding_approximation.approximate_generated_sota_rules_transformer import ApproximateGeneratedSotaRulesTransformer
from heuristic_splitter.grounding_approximation.approximate_generated_bdg_rules_transformer import ApproximateGeneratedBDGRulesTransformer
from heuristic_splitter.grounding_approximation.variable_domain_inference_transformer import VariableDomainInferenceTransformer

class GroundingStrategyHandler:

    def __init__(self, grounding_strategy: GroundingStrategyGenerator, rule_dictionary, graph_ds: GraphDataStructure):

        self.grounding_strategy = grounding_strategy
        self.rule_dictionary = rule_dictionary
        self.graph_ds = graph_ds

    def ground(self):

        grounded_program = ""
        domain_transformer = DomainTransformer()

        for level_index in range(len(self.grounding_strategy)):

            level = self.grounding_strategy[level_index]
            sota_rules = level["sota"]
            bdg_rules = level["bdg"]
            lpopt_rules = level["lpopt"]

            print(f"-- {level_index}: SOTA-RULES: {sota_rules}, BDG-RULES: {bdg_rules}")

            if len(bdg_rules) > 0:

                domain_transformer.update_domain_sizes()

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

                    print("-------------------------")
                    print(f"Rule: {rule}")
                    print(f"SOTA: {approximated_sota_rule_instantiations}")
                    print(f"BDG-OLD: {approximated_bdg_old_rule_instantiations}")
                    print(f"BDG-NEW: {approximated_bdg_new_rule_instantiations}")
                    print(f"USED-METHOD: {used_method}")
                    print("-------------------------")

                    if used_method == "SOTA":
                        sota_rules.append(bdg_rule)
                    else:
                        print("[ERROR] - Not yet implemented")
                        # TODO -> Call BDG procedure, depending on OLD/NEW BDG
                        raise NotImplementedError()

            if len(sota_rules) > 0:
                # Ground SOTA rules with SOTA (gringo/IDLV):
                decoded_string = self.start_gringo(grounded_program, sota_rules)

                parse_string(decoded_string, lambda stm: domain_transformer(stm))

                grounded_program = decoded_string

                print("+++++")
                print(sota_rules)
                print(decoded_string)
                print(domain_transformer.domain_dictionary)

        print("--- FINAL ---") 
        print(grounded_program)

    def start_gringo(self, grounded_program, rules, timeout=1800):

        program_input = grounded_program + "\n"
        for rule in rules:
            if rule in self.rule_dictionary:
                program_input += f"{str(self.rule_dictionary[rule])}\n"
            else:
                print(f"[ERROR] - Could not find rule {rule} in rule-dictionary.")
                raise NotImplementedError() # TBD Fallback

        print(program_input)


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

