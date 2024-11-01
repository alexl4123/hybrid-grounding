
from heuristic_splitter.rule import Rule
from heuristic_splitter.domain_inferer import DomainInferer

class CythonNagg:

    def __init__(self, domain : DomainInferer, custom_printer):

        self.domain = domain
        self.custom_printer = custom_printer

    
    def rewrite_rules(self, rules: [Rule]):

        for rule in rules:
            print(str(rule))