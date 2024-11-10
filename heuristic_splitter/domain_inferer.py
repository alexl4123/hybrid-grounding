
import re

class DomainInferer:

    def __init__(self):

        self.unsat_prg_found = False

        # These are not considered for domain inference:
        self.processed_literals = {}


        # A dict. of all domain values
        self.total_domain = {}

        """
        Definition of domain-dictionary:
        self.domain_dictionary[node.name] = {
            "tuples_size": Integer (Number of tuples)
            "terms": [POSITION IN LIST IS DOMAIN OF POSITION IN FUNCTION],
            "terms_size": [POSITION IN LIST IS DOMAIN-SIZE OF POSITION IN FUNCTION]
        }
        """
        self.domain_dictionary = {}

        self.minimum_term = None
        self.maximum_term = None

    def infer_processed_literals(self):

        for key in self.domain_dictionary.keys():
            self.processed_literals[key] = True 

    def try_parse_int(self, string):

        try:
            int_val = int(string)
            return int_val
        except ValueError:
            return None

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

                parsed_int = self.try_parse_int(term)
                if parsed_int is not None:    
                    if self.maximum_term is None or parsed_int > self.maximum_term:
                        self.maximum_term = parsed_int

                    if self.minimum_term is None or parsed_int < self.minimum_term:
                        self.minimum_term = parsed_int

        else:
            if str(term_tuple) not in self.domain_dictionary[constant_part]["tuples"]["maybe_true"]:
                self.domain_dictionary[constant_part]["tuples"]["maybe_true"][str(term_tuple)] = True
        
            for term_index in range(len(term_tuple)):
        
                term = term_tuple[term_index]
        
                if term not in self.domain_dictionary[constant_part]["terms"][term_index]:
                    self.domain_dictionary[constant_part]["terms"][term_index][term] = True
                if term not in self.total_domain:
                    self.total_domain[term] = True

    def compute_domain_average(self):
        """
        Computes an update of the tuple_size and term_size keys of the domain object.
        -> This is done for efficiencies sake (not to recompute this)
        """

        average = 0
        count = 0

        for _tuple in self.domain_dictionary.keys():
            if _tuple == "_average_domain_tuples":
                continue

            number_tuples = self.domain_dictionary[_tuple]["tuples_size"]

            domain_combinations = 1
            for _term_index in range(len(self.domain_dictionary[_tuple]["terms_size"])):

                terms_size = self.domain_dictionary[_tuple]["terms_size"][_term_index]

                domain_combinations *= terms_size

            percentage = number_tuples / domain_combinations

            count += 1
            average = average + (percentage - average) / (count)


        self.domain_dictionary["_average_domain_tuples"] = average
        


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

        