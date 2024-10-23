
import re

class GetFacts:

    def __init__(self):

        pass

    def get_facts_from_contents(self, contents):
        # Contents as a list of strings (rules):

        facts = {}
        facts_heads = {}
        all_heads = {}
        other_rules = []

        pattern_atom = re.compile(r'^(_?[a-z][A-Za-z0-9_´]*)\((.+?)\).*$')
        pattern_head_aggregate = re.compile(r'^.*{.*}.*$')
        pattern_rule = re.compile(r'^.*:-.*$')
        pattern_fact = re.compile(r'^(_?[a-z][A-Za-z0-9_´]*)\((.+?)\)\..*$')

        for content in contents:

            content = content.strip()

            # Find a match using re.match
            match = pattern_fact.match(content)

            if match:
                match2 = pattern_rule.match(content)
                if not match2: # Is surely a fact:
                    constant_part = match.group(1)  # The constant (e.g., '_test1')
                    arguments = match.group(2)      # The comma-separated part inside the parentheses (e.g., 'a,b')

                    # Split the arguments by commas
                    terms = arguments.split(",")
                    facts[constant_part + "(" + arguments + ")."] = True
                    facts_heads[constant_part] = True
                    all_heads[constant_part] = len(terms)
                    #print(f"Terms: {terms}")
                else:
                    if len(content) > 0:
                        other_rules.append(content)
            else:
                if len(content) > 0:
                    other_rules.append(content)
    
        return facts, facts_heads, other_rules
