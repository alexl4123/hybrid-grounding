# pylint: disable=C0103
"""
Necessary for Tuples Approx.
"""

import math

import clingo
from clingo.ast import Transformer

from heuristic_splitter.graph_data_structure import GraphDataStructure

from heuristic_splitter.program_structures.rule import Rule

from heuristic_splitter.grounding_approximation.variable_domain_size_inferer import VariableDomainSizeInferer


class ApproximateGeneratedSotaRules:
    """
    Approx. gen. tuples.
    """

    def __init__(self, domain_transformer, rule, alternative_global_number_terms = None, alternative_adjusted_tuples_per_arity = None):

        self.domain_transformer = domain_transformer
        self.alternative_global_number_terms = alternative_global_number_terms
        self.alternative_adjusted_global_tuples_per_arity = alternative_adjusted_tuples_per_arity

        self.rule = rule

        self.function_string = "FUNCTION"

        self.rule_tuples = 1

    def approximate_sota_size(self):

        # Necessary for variable intersections 
        processed_variables = {}

        domain = None
        domain_size_inferer = VariableDomainSizeInferer()
        variable_domain_sizes = None

        if self.domain_transformer is not None:
            domain = self.domain_transformer.domain_dictionary
            variable_domain_sizes = domain_size_inferer.get_variable_domain_size(self.rule, domain)

        for literal in self.rule.literals:
            if self.function_string in literal:
                if literal[self.function_string].in_head is False and literal[self.function_string].signum > 0:

                    function = literal[self.function_string]
                    # Only consider body stuff
                    # For the "b" and "c" in a :- b, not c.
                    # For the "e" in {a:b;c:d} :- e.
                    if domain is not None and function.name in domain and "terms" in domain[function.name]:
                        terms_domain = domain[function.name]["terms"]
                    elif domain is not None and "_total" in domain:
                        # Infer "_total" domain as an alternative (so the whole domain...)
                        terms_domain = domain["_total"]["terms"]
                    elif self.alternative_global_number_terms is not None and self.alternative_adjusted_global_tuples_per_arity is not None:
                        terms_domain = []
                    else:
                        raise Exception("_total domain not found!")

                    function_variables_domain_sizes = {}

                    domain_size_inferer.get_function_domain_size(function, terms_domain, function_variables_domain_sizes)

                    # Infer Number of Tuples:
                    if domain is not None and function.name in domain:
                        number_tuples = domain[function.name]["tuples_size"]
                    elif domain is not None:
                        average_tuples = domain["_average_domain_tuples"]
                        total_domain = len(self.domain_transformer.total_domain.keys())

                        arity = len(function.arguments)

                        combinations = 1
                        for _ in range(arity):
                            combinations *= total_domain
                        
                        number_tuples = int(math.ceil(average_tuples * combinations))
                    elif self.alternative_adjusted_global_tuples_per_arity is not None:
                        number_tuples = self.alternative_adjusted_global_tuples_per_arity
                    else:
                        raise Exception("[EROR] - Could not infer domain!")

                    tuples_function = number_tuples

                    variable_intersection_reduction_factor = 1

                    # Intersection of all previous variables with current variables.
                    # Which results in a "reduction" factor:
                    for variable in function_variables_domain_sizes:
                        if variable in processed_variables:
                            if domain is not None:
                                tmp_intersec_factor = variable_domain_sizes[variable]
                            elif self.alternative_global_number_terms is not None:
                                tmp_intersec_factor = self.alternative_global_number_terms
                            else:
                                raise Exception("[ERROR] - Could not infer domain!")

                            if tmp_intersec_factor > 0:
                                variable_intersection_reduction_factor *= tmp_intersec_factor

                        else:
                            # Variable not in domain --> Add it:
                            processed_variables[variable] = True

                    # ------------------------------------------------
                    # General join:
                    new_tuples = (tuples_function * self.rule_tuples)


                    # --------------------------------------------------
                    # Variable intersection join:
                    new_tuples = new_tuples / variable_intersection_reduction_factor

                    # -----------------------------------------
                    # Multiplicative addition of new-tuples:
                    self.rule_tuples = new_tuples

        return self.rule_tuples
