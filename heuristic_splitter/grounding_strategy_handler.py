
import subprocess

from clingo.ast import ProgramBuilder, parse_string

from heuristic_splitter.grounding_strategy_generator import GroundingStrategyGenerator
from heuristic_splitter.domain_transformer import DomainTransformer

class GroundingStrategyHandler:

    def __init__(self, grounding_strategy: GroundingStrategyGenerator, rule_dictionary):

        self.grounding_strategy = grounding_strategy
        self.rule_dictionary = rule_dictionary


    def ground(self):

        grounded_program = ""
        domain_transformer = DomainTransformer()

        for level_index in range(len(self.grounding_strategy)):

            level = self.grounding_strategy[level_index]
            sota_rules = level["sota"]

            print(f"-- {level_index}: {sota_rules}:")
            if len(sota_rules) > 0:
                decoded_string = self.start_gringo(sota_rules)

                parse_string(decoded_string, lambda stm: domain_transformer(stm))

                grounded_program += decoded_string

                print(decoded_string)
                print(domain_transformer.domain_dictionary)

            if len(bdg_rules) > 0:

                for bdg_rule in bdg_rules:

                    rule = self.rule_dictionary[bdg_rule]



        print("--- FINAL ---") 
        print(grounded_program)

    def start_gringo(self, rules, timeout=1800):

        program_input = ""
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

