
from heuristic_splitter.rule import Rule
from heuristic_splitter.domain_inferer import DomainInferer
from cython_nagg.generate_satisfiability_part import generate_satisfiability_part

class CythonNagg:

    def __init__(self, domain : DomainInferer, custom_printer):

        self.domain = domain
        self.custom_printer = custom_printer

    
    def rewrite_rules(self, rules: [Rule]):

        for rule in rules:
            print(str(rule))

            if rule.is_constraint is False:
                raise NotImplementedError("Foundedness and Head-Guess not (yet) implemented")

            generate_satisfiability_part(rule, self.domain)





