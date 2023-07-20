import time
import clingo
from enum import Enum

from clingo.ast import Transformer, Variable, parse_string, ProgramBuilder

from clingo.control import Control

from .aggregate_transformer import AggregateTransformer, AggregateMode
from .term_transformer import TermTransformer
from .domain_transformer import DomainTransformer
from .main_transformer import MainTransformer

class NormalStrategy(Enum):
    ASSUME_TIGHT = 1
    AUXILIARY = 2
    ORDERED_DERIVATION = 3

class Newground:

    def __init__(self, name="", no_show=False, ground_guess=False, ground=False, output_printer = None, aggregate_mode = AggregateMode.REPLACE, normal_mode = NormalStrategy.ASSUME_TIGHT):
        self.no_show = no_show
        self.ground_guess = ground_guess
        self.ground = ground
        self.output_printer = output_printer

        self.aggregate_mode = aggregate_mode
        self.normal_mode = normal_mode

        self.rules = False

    def start(self, contents):

        aggregate_transformer_output_program = self.start_aggregate_transformer(contents)

        domain, safe_variables, term_transformer = self.start_domain_inference(aggregate_transformer_output_program)

        self.start_main_transformation(aggregate_transformer_output_program, domain, safe_variables, term_transformer)

        

    def start_aggregate_transformer(self, contents):
 
        start_time = time.time()

        aggregate_transformer = AggregateTransformer(self.aggregate_mode)
        parse_string(contents, lambda stm: aggregate_transformer(stm))

        end_time = time.time()
        #print(f"[INFO] --> Newground aggregate_transformer_duration: {end_time - start_time}")

        shown_predicates = list(set(aggregate_transformer.shown_predicates))
        program_string = '\n'.join(shown_predicates + aggregate_transformer.new_prg)

        #print(program_string)
        #print("<<<<>>>>")
        #print("<<<<>>>>")
        #quit()

        if self.ground:
            self.output_printer.custom_print(contents)

        start_time = time.time()

        return program_string

    def start_domain_inference(self, combined_inputs):
        
        term_transformer = TermTransformer(self.output_printer, self.no_show)
        parse_string(combined_inputs, lambda stm: term_transformer(stm))

        safe_variables = term_transformer.safe_variable_rules
        domain = term_transformer.domain

        comparisons = term_transformer.comparison_operators_variables

        end_time = time.time()
        #print(f"[INFO] --> Newground term_transformer_duration: {end_time - start_time}")


        start_time = time.time()

        new_domain_hash = hash(str(domain))
        old_domain_hash = None
    
        while new_domain_hash != old_domain_hash:
        
            old_domain_hash = new_domain_hash

            domain_transformer = DomainTransformer(safe_variables, domain, comparisons)
            parse_string(combined_inputs, lambda stm: domain_transformer(stm))       

            safe_variables = domain_transformer.safe_variables_rules
            domain = domain_transformer.domain


            new_domain_hash = hash(str(domain))


        end_time = time.time()
        #print(f"[INFO] --> Newground domain_transformer_duration: {end_time - start_time}")

        return (domain, safe_variables, term_transformer)
       

    def start_main_transformation(self, aggregate_transformer_output_program, domain, safe_variables, term_transformer):
        start_time = time.time()


        ctl = Control()
        with ProgramBuilder(ctl) as bld:
            transformer = MainTransformer(bld, term_transformer.terms, term_transformer.facts,
                                          term_transformer.ng_heads, term_transformer.shows,
                                          self.ground_guess, self.ground, self.output_printer,
                                          domain, safe_variables, self.aggregate_mode)

            parse_string(aggregate_transformer_output_program, lambda stm: bld.add(transformer(stm)))

            end_time = time.time()
            #print(f"[INFO] --> Newground main_transformer_duration: {end_time - start_time}")



            if len(transformer.non_ground_rules.keys()) > 0:
                parse_string(":- not sat.", lambda stm: bld.add(stm))
                self.output_printer.custom_print(":- not sat.")

                sat_strings = []
                non_ground_rules = transformer.non_ground_rules
                for non_ground_rule_key in non_ground_rules.keys():
                    sat_strings.append(f"sat_r{non_ground_rule_key}")

    
                self.output_printer.custom_print(f"sat :- {','.join(sat_strings)}.")

                for key in transformer.unfounded_rules.keys():

                    unfounded_rules_heads = transformer.unfounded_rules[key]

                    sum_strings = []

                    for rule_key in unfounded_rules_heads.keys():

                        unfounded_rules_list = unfounded_rules_heads[rule_key]
                        unfounded_rules_list = list(set(unfounded_rules_list)) # Remove duplicates

                        sum_list = []
                        for index in range(len(unfounded_rules_list)):
                            unfounded_rule = unfounded_rules_list[index]
                            sum_list.append(f"1,{index} : {unfounded_rule}")

                        sum_strings.append(f"#sum{{{'; '.join(sum_list)}}} >=1 ")

                    
                    self.output_printer.custom_print(f":- {key}, {','.join(sum_strings)}.")
                
                if not self.ground_guess:
                    for t in transformer.terms:
                        self.output_printer.custom_print(f"dom({t}).")

                if not self.no_show:
                    if not term_transformer.show:
                        for f in transformer.shows.keys():
                            for l in transformer.shows[f]:
                                self.output_printer.custom_print(f"#show {f}/{l}.")



