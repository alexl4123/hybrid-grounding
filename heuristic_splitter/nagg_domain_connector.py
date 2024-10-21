

class TermTransformerMockup:

    def __init__(self, terms, shown_predicates):

        self.terms = terms
        self.shown_predicates = shown_predicates

class NaGGDomainConnector:

    def __init__(self, heuristic_domain, total_domain,nagg_safe_variables,shown_predicates ):

        self.heuristic_domain = heuristic_domain
        self.total_domain = total_domain
        self.nagg_domain = None
        self.nagg_safe_variables = None

        self.nagg_safe_variables = nagg_safe_variables

        self.shown_predicates = shown_predicates

        self.term_transformer = None
        

    def convert_data_structures(self):

        nagg_domain = {}
        for elem in self.heuristic_domain.keys():

            if elem in ["_average_domain_tuples"]:
                continue
            nagg_domain[elem] = {}
            print(elem)
            print(self.heuristic_domain[elem]["terms"])
            for position in range(len(self.heuristic_domain[elem]["terms"])):
                nagg_domain[elem][str(position)] = list(self.heuristic_domain[elem]["terms"][position].keys())

        nagg_domain["0_terms"] = list(self.total_domain.keys())

        self.nagg_domain = nagg_domain

        self.term_transformer = TermTransformerMockup(nagg_domain["0_terms"], self.shown_predicates)







    