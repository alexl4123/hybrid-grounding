# pylint: disable=C0103
"""
TODO
"""

import clingo
import itertools

from clingo.ast import Transformer

from heuristic_splitter.graph_data_structure import GraphDataStructure

from heuristic_splitter.rule import Rule


class NaGGDomainConnectorTransformer(Transformer):
    """
     TODO
    """

    def __init__(self, domain_transformer):

        self.domain_transformer = domain_transformer

        self.current_head = None
        self.current_function = None
        self.current_head_function = None

        self.node_signum = None

        self.head_is_choice_rule = False

        self.current_rule_position = 0
        self.current_function_position = 0

        self.in_body = False
        self.in_head = False

        self.shown_predicates = {}

        self.nagg_safe_variables = {}

        self.head_variables = {}
        self.variable_domains_in_function = {}
        self.variable_domains_helper = {}

        self.head_function = None



    def visit_Rule(self, node):
        """
        Visits an clingo-AST rule.
        """
        self.current_head = node.head

        if "body" in node.child_keys:
            self.in_body = True
            old = getattr(node, "body")
            self._dispatch(old)
            self.in_body = False

        if "head" in node.child_keys:
            self.in_head = True
            old = getattr(node, "head")
            self._dispatch(old)
            self.in_head = False

        if self.head_function is not None:
            # Domain Inference for BDG:

            self.domain_transformer.domain_dictionary[self.head_function] = {
                "tuples": {
                    "sure_true": {},
                    "maybe_true": {
                    },
                },
                "terms": []
            }

            dom_list = []
            for variable in self.head_variables.keys():
                self.domain_transformer.domain_dictionary[self.head_function]["terms"].append({})
                dom_list.append([])
            
            for variable in self.head_variables.keys():
                variable_index = self.head_variables[variable]

                for term in self.variable_domains_helper[variable]:
                    self.domain_transformer.domain_dictionary[self.head_function]["terms"][variable_index][term] = True
        
                    if term not in self.domain_transformer.total_domain:
                        self.total_domain[term] = True

                    dom_list[variable_index].append(term)

            for term_tuple in itertools.product(*dom_list):
                self.domain_transformer.domain_dictionary[self.head_function]["tuples"]["maybe_true"][str(list(term_tuple))] = True


        self.current_rule_position += 1
        self._reset_temporary_rule_variables()
        return node

    def visit_Function(self, node):
        """
        Visits an clingo-AST function.
        """
        self.current_function = node

        self.visit_children(node)

        if str(node) not in self.shown_predicates:

            arity = len(list(str(node).split(",")))

            self.shown_predicates[str(node.name)] = {arity}

        if self.in_body:
            # Only consider body stuff
            # For the "b" and "c" in a :- b, not c.
            # For the "e" in {a:b;c:d} :- e.

            for variable in self.variable_domains_in_function.keys():

                if variable in self.variable_domains_helper:

                    # Domain Intersection:
                    self.variable_domains_helper[variable] = set(list(self.variable_domains_helper[variable])).intersection(set(list(self.variable_domains_in_function[variable])))

                else:
                    # Variable not in domain --> Add it:
                    self.variable_domains_helper[variable] = list(self.variable_domains_in_function[variable].keys())
        elif self.in_head:
            self.head_function = node.name

        self._reset_temporary_function_variables()
        return node

    def visit_Variable(self, node):
        """
        Visits an clingo-AST variable.
        Takes care of most things about domain-inference.
        """

        self.visit_children(node)

        if self.in_body is True and self.node_signum > 0 and self.current_function is not None:

            if self.current_rule_position not in self.nagg_safe_variables:
                self.nagg_safe_variables[self.current_rule_position] = {}

            if str(node) not in self.nagg_safe_variables[self.current_rule_position]:
                self.nagg_safe_variables[self.current_rule_position][str(node)] = []

            to_add_dict = {}
            to_add_dict["type"] = "function"
            to_add_dict["name"] = str(self.current_function.name)
            to_add_dict["position"] = str(self.current_function_position)
            to_add_dict["signum"] = str(0) # NaGG uses 0 as positive, but the heuristics +1

            self.nagg_safe_variables[self.current_rule_position][str(node)].append(to_add_dict)


        if self.in_body is True:
            if self.current_function is not None and self.current_function.name in self.domain_transformer.domain_dictionary:
                if node.name not in self.variable_domains_in_function:
                    self.variable_domains_in_function[node.name] = self.domain_transformer.domain_dictionary[self.current_function.name]["terms"][self.current_function_position]
                elif len(self.variable_domains_in_function[node.name].keys()) > len(self.domain_transformer.domain_dictionary[self.current_function.name]["terms"][self.current_function_position].keys()):
                    self.variable_domains_in_function[node.name] = self.domain_transformer.domain_dictionary[self.current_function.name]["terms"][self.current_function_position]
            else:
                self.variable_domains_in_function[node.name] = self.domain_transformer.total_domain           

        elif self.in_head is True:
            self.head_variables[node.name] = self.current_function_position



        self.current_function_position += 1

        return node

    def visit_SymbolicTerm(self, node):
        """
        Visits an clingo-AST symbolic term (constant).
        """
        if self.current_function:

            self.current_function_position += 1

        return node

    def visit_Literal(self, node):
        """
        Visits a clingo-AST literal (negated/non-negated).
        -> 0 means positive
        -> -1 means negative
        """

        if node.sign == 0:
            self.node_signum = +1
        else:
            # Do not consider literal if negative
            self.node_signum = -1

        self.visit_children(node)

        self._reset_temporary_literal_variables()

        return node

    def _reset_temporary_literal_variables(self):
        self.node_signum = None

    def _reset_temporary_aggregate_variables(self):
        self.head_element_index = 0

    def _reset_temporary_rule_variables(self):
        self.current_head = None
        self.current_head_function = None
        self.head_is_choice_rule = False

    def _reset_temporary_function_variables(self):
        self.current_function = None
        self.current_function_position = 0

        self.variable_domains_in_function = {}


