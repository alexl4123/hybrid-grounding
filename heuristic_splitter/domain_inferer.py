
import re

class DomainInferer:

    def __init__(self):

        self.unsat_prg_found = False


        # A dict. of all domain values
        self.total_domain = {}

        """
        Definition of domain-dictionary:
        ------------
        self.domain_dictionary[node.name] = {
            "tuples": {
                "sure_true": {...},
                "maybe_true": {
                    str(TUPLE): True
                },
            },
            "tuples_size": {
                "sure_true": INT VALUE,
                "maybe_true": INT VALUE
            }
            "terms": [POSITION IN LIST IS DOMAIN OF POSITION IN FUNCTION],
            "terms_size": [POSITION IN LIST IS DOMAIN-SIZE OF POSITION IN FUNCTION]
        }
        for term in term_tuple:
            -> Here the terms are added
            self.domain_dictionary[node.name]["terms"].append({term:True})
        """
        self.domain_dictionary = {}

    def add_node_to_domain(self, arguments, constant_part):
        # Split the arguments by commas
        term_tuple = list(arguments.split(','))
        
        if constant_part not in self.domain_dictionary:
            self.domain_dictionary[constant_part] = {
                "tuples": {
                    "sure_true": {},
                    "maybe_true": {
                        str(term_tuple): True
                    },
                },
                "terms": []
            }
            for term in term_tuple:
                self.domain_dictionary[constant_part]["terms"].append({term:True})
        
                if term not in self.total_domain:
                    self.total_domain[term] = True
        else:
            if str(term_tuple) not in self.domain_dictionary[constant_part]["tuples"]["maybe_true"]:
                self.domain_dictionary[constant_part]["tuples"]["maybe_true"][str(term_tuple)] = True
        
            for term_index in range(len(term_tuple)):
        
                term = term_tuple[term_index]
        
                if term not in self.domain_dictionary[constant_part]["terms"][term_index]:
                    self.domain_dictionary[constant_part]["terms"][term_index][term] = True
                if term not in self.total_domain:
                    self.total_domain[term] = True

    def infer_domain(self, contents):
        # Contents as a list of strings (rules):

        facts = {}
        facts_heads = {}
        other_rules = []

        pattern_atom = re.compile(r'^(_?[a-z][A-Za-z0-9_´]*)\((.+?)\).*$')
        pattern_head_aggregate = re.compile(r'^.*{.*}.*$')
        pattern_rule = re.compile(r'^.*:-.*$')

        for content in contents.split("\n"):

            head = content.split(":-")[0]
            atom_match = pattern_atom.match(head)
            if atom_match:
                # Head is atom
                constant_part = atom_match.group(1)  # The constant (e.g., '_test1')
                arguments = atom_match.group(2)      # The comma-separated part inside the parentheses (e.g., 'a,b')

                #self.add_node_to_domain(arguments, constant_part)
                self.add_node_to_domain(arguments, constant_part)

            elif pattern_head_aggregate.match(head):
                # Head is head-aggregate

                head_aggregate_elements = head.split("{")[1]
                head_aggregate_elements = head_aggregate_elements.split("}")[0]
                head_aggregate_elements = head_aggregate_elements.split(";")

                for element in head_aggregate_elements:

                    element_head = element.split(":")[0]

                    atom_match = pattern_atom.match(element_head)
                    if atom_match:
                        # Head is atom
                        constant_part = atom_match.group(1)  # The constant (e.g., '_test1')
                        arguments = atom_match.group(2)      # The comma-separated part inside the parentheses (e.g., 'a,b')

                        self.add_node_to_domain(arguments, constant_part)
                    elif "<=>" in head:
                        continue
                    else:
                        print(f"[ERROR] - Failed to parse head-aggregate: {head}")
                        raise NotImplementedError()

            elif len(head.strip()) == 0 or head.strip() == "#false":
                if content.strip() == ":-.":
                    self.unsat_prg_found = True

                continue
            elif "(" not in head:
                # Atom
                continue
            elif "#delayed" in head or "#show" in head:
                continue
            else:
                print(content)
                raise NotImplementedError("HEAD NOT IMPLEMENTED!")

    def update_domain_sizes(self):
        """
        Computes an update of the tuple_size and term_size keys of the domain object.
        -> This is done for efficiencies sake (not to recompute this)
        """

        average = 0
        count = 0

        for _tuple in self.domain_dictionary.keys():
            if _tuple == "_average_domain_tuples":
                continue

            self.domain_dictionary[_tuple]["tuples_size"] = {}

            number_sure_tuples = len(self.domain_dictionary[_tuple]["tuples"]["sure_true"].keys())
            self.domain_dictionary[_tuple]["tuples_size"]["sure_true"] = number_sure_tuples
            number_maybe_tuples = len(self.domain_dictionary[_tuple]["tuples"]["maybe_true"].keys())
            self.domain_dictionary[_tuple]["tuples_size"]["maybe_true"] = number_maybe_tuples

            self.domain_dictionary[_tuple]["terms_size"] = []

            domain_combinations = 1

            for _term_index in range(len(self.domain_dictionary[_tuple]["terms"])):

                terms_size = len(self.domain_dictionary[_tuple]["terms"][_term_index].keys())
                self.domain_dictionary[_tuple]["terms_size"].append(terms_size)

                domain_combinations *= terms_size

            percentage = (number_sure_tuples + number_maybe_tuples) / domain_combinations

            average = average + (percentage - average) / (count + 1)

        self.domain_dictionary["_average_domain_tuples"] = average
        



    def parse_smodels_literal(self, literal):

        pattern_id = re.compile(r'(_?[a-z][A-Za-z0-9_´]*)')

        literal = literal.strip()
        match = pattern_id.search(literal)
        if match:
            _id = match.group()

            arguments = literal[len(_id):]
            if len(arguments) > 0 and arguments[0] == "(":
                arguments = arguments[1:]
                arguments = arguments[:-1]

            self.add_node_to_domain(arguments, _id)

        