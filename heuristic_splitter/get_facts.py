
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

        pattern_fact = re.compile(r'^(_?[a-z][A-Za-z0-9_´]*)\((.+?)\).*$')

        for content in contents:

            content = content.strip()

            if ":-" not in content:
                content = content.split("%")[0] # Remove comments that start at the beginning
                content = content.split("#")[0] # Remove program statements for now

                if "(" in content and "{" not in content:
                    # Find a match using re.match
                    match = pattern_fact.match(content)
                    if match:
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
                
                elif len(content) == 0:
                    continue # Is empty line
                elif "{" not in content:
                    facts[content] = True
                    facts_heads[content.split(".")[0]] = True
                    all_heads[content.split(".")[0]] = 0
                else:
                    if len(content) > 0:
                        other_rules.append(content)
            else:
                content = content.split("%")[0] # Remove comments that start at the beginning
                #content = content.split("#")[0] # Remove program statements for now
                if len(content) > 0:
                    other_rules.append(content)
                        
        return facts, facts_heads, other_rules, all_heads
