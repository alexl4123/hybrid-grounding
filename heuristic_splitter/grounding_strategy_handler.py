
import io
import time
import sys
import os
import subprocess
import gc

import tempfile

from clingo.ast import ProgramBuilder, parse_string

from heuristic_splitter.graph_data_structure import GraphDataStructure

from heuristic_splitter.grounding_strategy_generator import GroundingStrategyGenerator
from heuristic_splitter.domain_transformer import DomainTransformer

from heuristic_splitter.grounding_approximation.approximate_generated_sota_rules_transformer import ApproximateGeneratedSotaRulesTransformer
from heuristic_splitter.grounding_approximation.approximate_generated_bdg_rules_transformer import ApproximateGeneratedBDGRulesTransformer
from heuristic_splitter.grounding_approximation.variable_domain_inference_transformer import VariableDomainInferenceTransformer

from heuristic_splitter.nagg_domain_connector_transformer import NaGGDomainConnectorTransformer
from heuristic_splitter.nagg_domain_connector import NaGGDomainConnector

from heuristic_splitter.program.preprocess_smodels_program import preprocess_smodels_program

from nagg.default_output_printer import DefaultOutputPrinter

from nagg.nagg import NaGG
from nagg.aggregate_strategies.aggregate_mode import AggregateMode
from nagg.cyclic_strategy import CyclicStrategy
from nagg.grounding_modes import GroundingModes
from nagg.foundedness_strategy import FoundednessStrategy
from heuristic_splitter.domain_inferer import DomainInferer

from heuristic_splitter.program.string_asp_program import StringASPProgram
from heuristic_splitter.program.smodels_asp_program import SmodelsASPProgram

from cython_nagg.cython_nagg import CythonNagg
from cython_nagg.justifiability_type import JustifiabilityType

from ctypes import *
so_file = "./heuristic_splitter/c_output_redirector.so"

# C-Struct (return value)
class PipeFds(Structure):
    _fields_ = [("read_end", c_int), ("write_end", c_int)]


class CustomOutputPrinter(DefaultOutputPrinter):

    def __init__(self):
        self.strings = []

    def custom_print(self, string):
        #print(string)
        self.strings.append(string)

    def get_string(self):
        return "\n".join(self.strings)

class GroundingStrategyHandler:

    def __init__(self, grounding_strategy: GroundingStrategyGenerator, rule_dictionary, graph_ds: GraphDataStructure, facts, query,
        debug_mode, enable_lpopt, output_printer = None, enable_logging = False, logging_file = None):

        self.grounding_strategy = grounding_strategy
        self.rule_dictionary = rule_dictionary
        self.facts = facts
        self.query = query
        
        self.graph_ds = graph_ds

        self.debug_mode = debug_mode
        self.enable_lpopt = enable_lpopt
        self.output_printer = output_printer

        self.enable_logging = enable_logging
        self.logging_file = logging_file

        self.grounded_program = None

        self.grd_call = 0
        self.total_nagg_calls = 0

    def single_ground_call(self, all_heads):

        if self.grounded_program is None: 
            self.grounded_program = StringASPProgram("\n".join(list(self.facts.keys())))

        domain_transformer = DomainInferer()
        if len(self.grounding_strategy) > 0:
            # Ground SOTA rules with SOTA (gringo/IDLV):
            sota_rules_string = self.rule_list_to_rule_string(self.grounding_strategy[0]["sota"]) 

            if self.enable_logging is True:
                self.logging_file.write("All rules were grounded via SOTA approaches:")
                self.logging_file.write(sota_rules_string)

            program_input = self.grounded_program.get_string() + "\n" + sota_rules_string

            decoded_string = self.start_sota_grounder(program_input, output_mode="--output=smodels")

            self.grounded_program = SmodelsASPProgram(self.grd_call)
            self.grounded_program.preprocess_smodels_program(decoded_string, domain_transformer)
            gringo_string = self.grounded_program.get_string(insert_flags=True)
        else:
            gringo_string = self.grounded_program.get_string()

        if self.debug_mode is True:
            print("--- FINAL ---") 

        show_statements = "\n".join([f"#show {key}/{all_heads[key]}." for key in all_heads.keys()] + [f"#show -{key}/{all_heads[key]}." for key in all_heads.keys()])
        query_statement = ""
        if len(self.query.keys()) > 0:
            query_statement = list(self.query.keys())[0]
        final_string = gringo_string + "\n" + show_statements + "\n" + query_statement

        if self.output_printer:
            self.output_printer.custom_print(final_string)
        else:
            print(final_string)

    def ground(self):

        c_output_redirector = CDLL(so_file)
        # Set the return type of open_pipe to our struct
        c_output_redirector.open_pipe.restype = PipeFds

        if self.enable_logging is True:
            self.logging_file.write("-------------------------------------------------------\n")
            self.logging_file.write("The following is the final grounding strategy:\n")
            self.logging_file.write(str(self.grounding_strategy))
            self.logging_file.write("-------------------------------------------------------\n")

        domain_inference_called_at_least_once = False

        if self.grounded_program is None: 
            self.grounded_program = StringASPProgram("\n".join(list(self.facts.keys())))

        # Explicitly invoke garbage collection (I do not need facts anymore) 
        del self.facts
        gc.collect()

        domain_transformer = DomainInferer()

        level_index = 0
        while level_index < len(self.grounding_strategy):

            if domain_transformer.unsat_prg_found is True:
                break

            level = self.grounding_strategy[level_index]
            sota_rules = level["sota"]
            bdg_rules = level["bdg"]


            if self.debug_mode is True:
                print(f"-- {level_index}: SOTA-RULES: {sota_rules}, BDG-RULES: {bdg_rules}")

            if len(bdg_rules) > 0 and domain_inference_called_at_least_once is True:

                #domain_transformer.update_domain_sizes()
                tmp_bdg_old_found_rules = []
                tmp_bdg_new_found_rules = []

                for bdg_rule in bdg_rules:

                    rule = self.rule_dictionary[bdg_rule]

                    if rule.in_program_rules is True:
                        # TDB -> TODO
                        tmp_bdg_new_found_rules.append(bdg_rule)
                    else:
                        approx_number_rules, used_method, rule_str = self.get_best_method_by_approximated_rule_count(domain_transformer, rule)

                        if used_method == "SOTA":
                            sota_rules.append(bdg_rule)
                        elif used_method == "BDG_OLD":
                            tmp_bdg_old_found_rules.append(bdg_rule)
                        else:
                            tmp_bdg_new_found_rules.append(bdg_rule) 

                no_show = True
                ground_guess = True
                # Custom printer keeps result of prototype (NaGG)
                aggregate_mode = AggregateMode.RA
                cyclic_strategy = CyclicStrategy.LEVEL_MAPPING
                grounding_mode = GroundingModes.REWRITE_AGGREGATES_GROUND_FULLY

                if len(tmp_bdg_new_found_rules) > 0:
                    program_input = self.rule_list_to_rule_string(tmp_bdg_new_found_rules)

                    if self.enable_logging is True:
                        self.logging_file.write("-------------------------------------------------------\n")
                        self.logging_file.write("The following rules were grounded via BDG NEW approach:\n")
                        self.logging_file.write(tmp_rules_string)

                    input_rules = []
                    for bdg_rule in bdg_rules:
                        input_rules.append(self.rule_dictionary[bdg_rule])

                    start_time = time.time()

                    # Create a tmpfile for stdout redirect.
                    fd, path = tempfile.mkstemp()

                    try:
                        stdout_backup = c_output_redirector.redirect_stdout_to_fd_and_duplicate_and_close(fd)

                        cython_nagg = CythonNagg(domain_transformer,
                            nagg_call_number=self.total_nagg_calls, justifiability_type=JustifiabilityType.SATURATION)
                        cython_nagg.rewrite_rules(input_rules)
                        end_time = time.time()

                        c_output_redirector.call_flush()
                        pipe_write_backup = c_output_redirector.redirect_stdout_to_fd_and_duplicate_and_close(stdout_backup)

                        os.close(pipe_write_backup)
                        f = open(path, "r")
                        output = f.read()

                        f.close()

                        self.grounded_program.add_string(output)

                    except Exception as ex:

                        print(ex)
                        raise ex

                    finally:
                        os.remove(path)

                    if self.enable_logging is True:
                        print(f"---> TIME DURATION CYTHON NAGG NEW: {end_time - start_time}", file=sys.stderr)

                    self.total_nagg_calls += 1

                if len(tmp_bdg_old_found_rules) > 0:

                    program_input = self.rule_list_to_rule_string(tmp_bdg_old_found_rules)

                    if self.enable_logging is True:
                        self.logging_file.write("-------------------------------------------------------\n")
                        self.logging_file.write("The following rules were grounded via BDG OLD approach:\n")
                        self.logging_file.write(tmp_rules_string)

                    input_rules = []
                    for bdg_rule in bdg_rules:
                        input_rules.append(self.rule_dictionary[bdg_rule])

                    start_time = time.time()

                    # Create a tmpfile for stdout redirect.
                    fd, path = tempfile.mkstemp()

                    try:
                        stdout_backup = c_output_redirector.redirect_stdout_to_fd_and_duplicate_and_close(fd)

                        cython_nagg = CythonNagg(domain_transformer,
                            nagg_call_number=self.total_nagg_calls, justifiability_type=JustifiabilityType.UNFOUND)
                        cython_nagg.rewrite_rules(input_rules)
                        end_time = time.time()

                        c_output_redirector.call_flush()
                        pipe_write_backup = c_output_redirector.redirect_stdout_to_fd_and_duplicate_and_close(stdout_backup)

                        os.close(pipe_write_backup)
                        f = open(path, "r")
                        output = f.read()

                        f.close()

                        self.grounded_program.add_string(output)

                    except Exception as ex:

                        print(ex)
                        raise ex

                    finally:
                        os.remove(path)




                    if self.enable_logging is True:
                        print(f"---> TIME DURATION CYTHON NAGG NEW: {end_time - start_time}", file=sys.stderr)

                    self.total_nagg_calls += 1


                    
            if len(sota_rules) > 0 or domain_inference_called_at_least_once is False:

                if len(sota_rules) == 0 and domain_inference_called_at_least_once is False:
                    level_index -= 1

                domain_inference_called_at_least_once = True

                # Ground SOTA rules with SOTA (gringo/IDLV):
                sota_rules_string = self.rule_list_to_rule_string(sota_rules) 

                if self.enable_logging is True:
                    self.logging_file.write("-------------------------------------------------------\n")
                    self.logging_file.write("The following rules were grounded via SOTA approaches:\n")
                    self.logging_file.write(sota_rules_string)

                program_input = self.grounded_program.get_string() + "\n" + sota_rules_string

                # Explicitly garbage collect stuff
                del self.grounded_program
                gc.collect()

                decoded_string = self.start_sota_grounder(program_input)

                #parse_string(decoded_string, lambda stm: domain_transformer(stm))
                self.grounded_program = SmodelsASPProgram(self.grd_call)
                self.grounded_program.preprocess_smodels_program(decoded_string, domain_transformer)

                self.grd_call += 1
                #domain_transformer.infer_domain(decoded_string)

                if self.debug_mode is True:
                    print("+++++")
                    print(sota_rules)
                    print(sota_rules_string)
                    print("++")
                    print(decoded_string)
                    print(domain_transformer.domain_dictionary)

            level_index += 1
        

    def output_grounded_program(self, all_heads):

        if self.debug_mode is True:
            print("--- FINAL ---") 

        show_statements = "\n".join([f"#show {key}/{all_heads[key]}." for key in all_heads.keys()] + [f"#show -{key}/{all_heads[key]}." for key in all_heads.keys()])

        query_statement = ""
        if len(self.query.keys()) > 0:
            query_statement = list(self.query.keys())[0]

        input_program = self.grounded_program.get_string(insert_flags=True) + "\n" + show_statements + "\n" + query_statement


        #final_program = self.start_gringo(input_program, output_mode="--output=smodels")
        if self.output_printer:
            self.output_printer.custom_print(input_program)
        else:
            print(input_program)

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


    def start_sota_grounder(self, program_input, timeout=1800, output_mode = "--output=smodels", grounder="gringo"):

        if grounder == "idlv":
            arguments = ["./idlv.bin", "--output=0", "--stdin"]
        elif grounder == "gringo":
            arguments = ["gringo", "--output=smodels"]
        else:
            raise NotImplementedError(f"Grounder {grounder} not implemented!")

        decoded_string = ""
        try:
            p = subprocess.Popen(arguments, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)       
            (ret_vals_encoded, error_vals_encoded) = p.communicate(input=bytes(program_input, "ascii"), timeout = timeout)

            decoded_string = ret_vals_encoded.decode()
            error_vals_decoded = error_vals_encoded.decode()

            if p.returncode != 0 and p.returncode != 10 and p.returncode != 20 and p.returncode != 30:
                print(f">>>>> Other return code than 0 in helper: {p.returncode}")
                print(error_vals_decoded)
                raise Exception(error_vals_decoded)

        except Exception as ex:
            print(program_input)
            try:
                p.kill()
            except Exception as e:
                pass

            raise Exception(ex) # TBD: Continue if possible

        return decoded_string
