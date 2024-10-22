
import re

class GetFacts:

    def __init__(self):

        pass

    def get_facts_from_contents(self, contents):
        # Contents as a list of strings (rules):

        facts = {}
        facts_heads = {}
        other_rules = []

        pattern = re.compile(r'^(_?[a-z][A-Za-z0-9_´]*)\((.+?)\)\..*$')
        pattern2 = re.compile(r'^.*:-.*$')

        for content in contents:

            # Find a match using re.match
            match = pattern.match(content)

            if match:
                match2 = pattern2.match(content)
                if not match2: # Is surely a fact:
                    constant_part = match.group(1)  # The constant (e.g., '_test1')
                    arguments = match.group(2)      # The comma-separated part inside the parentheses (e.g., 'a,b')

                    # Split the arguments by commas
                    terms = arguments.split(',')
                    facts[constant_part + "(" + arguments + ")."] = True
                    facts_heads[constant_part] = True
                    #print(f"Terms: {terms}")
            else:
                other_rules.append(content)
    
        return facts, facts_heads, other_rules
