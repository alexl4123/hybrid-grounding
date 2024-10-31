
from heuristic_splitter.domain_inferer import DomainInferer
from heuristic_splitter.program.asp_program import ASPProgram

from heuristic_splitter.program.preprocess_smodels_program import preprocess_smodels_program as cython_preprocess_smodels_program

class SmodelsASPProgram(ASPProgram):

    def __init__(self, grd_call, debug_mode = False):

        self.program = []
        self.literals_dict = {}
        self.debug_mode = debug_mode

        self.other_prg_string = ""

        self.auxiliary_name = f"auxiliary_{grd_call}_"

        # As IDLV is not able to handle #inf and #sup as input:
        self.sup_flag = "sup_flag"
        self.inf_flag = "inf_flag"

        self.global_weight_index = 0


    def preprocess_smodels_program(self, smodels_program_string, domain_inferer: DomainInferer):
    
        rules, domain_dictionary, total_domain, literals_dict = cython_preprocess_smodels_program(smodels_program_string, domain_inferer.processed_literals)

        self.program = rules
        self.literals_dict = literals_dict

        domain_inferer.domain_dictionary = domain_inferer.domain_dictionary | domain_dictionary
        domain_inferer.total_domain = domain_inferer.total_domain | total_domain

        domain_inferer.infer_processed_literals()
        domain_inferer.compute_domain_average()

    def preprocess_smodels_programs_approximate_python(self, smodels_program_string, domain_inferer: DomainInferer):

        part = "program"

        for line in smodels_program_string.split("\n"):

            line = line.strip()

            if line == "0":
                if part == "program":
                    part = "symbol_table"
                elif part == "symbol_table":
                    part = "computation"
                else:
                    continue
            elif part == "program":
                self.program.append(line)
            elif part == "symbol_table":
                splits = line.split(" ")

                symbol = splits[0]
                literal = " ".join(splits[1:])

                if "#sup" in literal:
                    literal = literal.replace("#sup", self.sup_flag)

                if "#inf" in literal:
                    literal = literal.replace("#inf", self.inf_flag)

                self.literals_dict[symbol] = literal

                domain_inferer.parse_smodels_literal(literal)


            else:
                continue

    def add_string(self, to_add_prg):
        """
        To handle compability with NaGG (NaGG output is string).
        """

        self.other_prg_string = self.other_prg_string + to_add_prg

    def get_string(self, insert_flags = False):

        if self.debug_mode is True:
            print("+++++ START REWRITING SMODELS OUTPUT +++++")

        parsed_rules = []
        for rule in self.program:
            if self.debug_mode is True:
                print(rule)

            if rule[0] == 1:
                # Normal Rule
                parsed_rule = self.handle_normal_rule(rule, insert_flags)
                if self.debug_mode is True:
                    print(parsed_rule)
                parsed_rules.append(parsed_rule)
            elif rule[0] == 2:
                # Constraint Rule
                parsed_rule = self.handle_smodels_constraint_rule(rule, insert_flags)
                if self.debug_mode is True:
                    print(parsed_rule)
                parsed_rules.append(parsed_rule)
            elif rule[0] == 3:
                # Choice Rule
                parsed_rule = self.handle_smodels_choice_rule(rule, insert_flags)
                if self.debug_mode is True:
                    print(parsed_rule)
                parsed_rules.append(parsed_rule)
            elif rule[0] == 4: 
                raise Exception("Was never defined!")
            elif rule[0] == 5:
                # Weight Rule
                parsed_rule = self.handle_smodels_weight_rule(rule, insert_flags)
                if self.debug_mode is True:
                    print(parsed_rule)
                parsed_rules.append(parsed_rule)
            elif rule[0] == 6:
                # Weak Constraint
                self.handle_smodels_weak_constraint(rule, insert_flags, parsed_rules)
            elif rule[0] == 8:
                # Disjunctive Rule
                parsed_rule = self.handle_smodels_disjunctive_head_rule(rule, insert_flags)
                if self.debug_mode is True:
                    print(parsed_rule)
                parsed_rules.append(parsed_rule)
            else:
                print(rule)
                raise NotImplementedError(f"SMODELS Rule not implemented {rule}")

        # Constraint handling:
        parsed_rule = f":- {self.auxiliary_name}1."
        parsed_rules.append(parsed_rule)
        if self.debug_mode is True:
            print(parsed_rule)
            print("+++++ END REWRITING SMODELS OUTPUT +++++")

        self.global_weight_index = 0

        return "\n".join(parsed_rules) + self.other_prg_string

    def handle_normal_rule(self, symbols, insert_flags):
        """
        -- Handle smodels rule with type 1:
        SYNAPSIS: 1 head #literals #negative negative positive
        """

        head_symbol = symbols[1]

        number_body_literals = symbols[2]
        number_negative_body_literals = symbols[3]

        if number_body_literals == 0:
            return self.infer_symbol_name(head_symbol, insert_flags) + "."
        else:
            head = self.infer_symbol_name(head_symbol, insert_flags)

            body_string_list = []
            remaining_body_literals = symbols[4:]

            for body_symbol in remaining_body_literals:

                body_literal = self.infer_symbol_name(body_symbol, insert_flags)

                if len(body_string_list) < number_negative_body_literals:
                    body_string_list.append("not " + body_literal)
                else:
                    body_string_list.append(body_literal)


            body = ",".join(body_string_list)

            return head + " :- " + body + "."


    def handle_smodels_constraint_rule(self, symbols, insert_flags):
        """
        -- Handle an SMODELS constraint rule (not an ASP constraint)
        SYNAPSIS: 2 head #literals #negative bound negative positive
        CORRESPONDS TO: head :- bound <= #count{literal0; literal1; ...}
        OR SIMPLIFIED: head :- bound {literal0; literal1; ...}
        """

        head_symbol = symbols[1]

        number_body_literals = symbols[2]
        number_negative_body_literals = symbols[3]
        bound = symbols[4]

        if number_body_literals == 0:
            return self.infer_symbol_name(head_symbol, insert_flags) + "."
        else:
            head = self.infer_symbol_name(head_symbol, insert_flags)

            body_string_list = []
            remaining_body_literals = symbols[5:]

            for body_symbol in remaining_body_literals:

                body_literal = self.infer_symbol_name(body_symbol, insert_flags)

                if len(body_string_list) < number_negative_body_literals:
                    body_string_list.append("not " + body_literal)
                else:
                    body_string_list.append(body_literal)


            body = ";".join([f"1,{index}:{body_string_list[index]}" for index in range(len(body_string_list))])

            return head + " :- " + str(bound) + " <= #count{" + body + "}."

    
    def handle_smodels_choice_rule(self, symbols, insert_flags):
        """
        -- Handle an SMODELS choice rule
        SYNAPSIS: 3 #heads heads #literals #negative negative positive
        CORRESPONDS TO: {heads} :- body 
        """

        heads = symbols[1]

        heads_list = []
        head_string_index = 2

        for head_index in range(heads):

            head_string_index = 2 + head_index

            head_symbol = symbols[head_string_index]

            heads_list.append(self.infer_symbol_name(head_symbol, insert_flags))

        
        head_string = "{" + ";".join(heads_list) + "}"

        body_start_string_index = head_string_index + 1

        number_body_literals = symbols[body_start_string_index]
        number_negative_body_literals = symbols[body_start_string_index + 1]

        if number_body_literals == 0:
            return head_string + "."
        else:

            body_string_list = []
            remaining_body_literals = symbols[body_start_string_index + 2:]

            for body_symbol in remaining_body_literals:

                body_literal = self.infer_symbol_name(body_symbol, insert_flags)

                if len(body_string_list) < number_negative_body_literals:
                    body_string_list.append("not " + body_literal)
                else:
                    body_string_list.append(body_literal)


            body = ",".join(body_string_list)

            return head_string + " :- " + body + "."


    def handle_smodels_weight_rule(self, symbols, insert_flags):
        """
        -- Handle SMODELS weight rule.
        SYNPOSIS: 5 head bound #lits #negative negative positive weights
        """

        head_symbol = symbols[1]
        bound = symbols[2]
        number_body_literals = symbols[3]
        number_negative_body_literals = symbols[4]

        if number_body_literals == 0:
            return self.infer_symbol_name(head_symbol, insert_flags) + "."
        else:
            head = self.infer_symbol_name(head_symbol, insert_flags)

            body_string_list = []
            remaining_body_literals = symbols[5:]

            for body_symbol_index in range(number_body_literals):

                body_symbol = remaining_body_literals[body_symbol_index]
                body_literal = self.infer_symbol_name(body_symbol, insert_flags)

                if len(body_string_list) < number_negative_body_literals:
                    body_string_list.append("not " + body_literal)
                else:
                    body_string_list.append(body_literal)

            weights = []
            for weight_body_symbol_index in range(number_body_literals, number_body_literals * 2):
                weight = remaining_body_literals[weight_body_symbol_index]
                weights.append(weight)

            body = ";".join([f"{weights[index]},{index}:{body_string_list[index]}" for index in range(len(weights))])

            return head + " :- " + str(bound) + " <= #sum{" + body + "}."

    def handle_smodels_weak_constraint(self, symbols, insert_flags, parsed_rules):
        """
        -- Handle smodels rule with type 6:
        SYNAPSIS: 6 0 #lits #negative negative positive weights
        --> Different than most rules, as this rule has changed syntax in modern ASP
        --> We must infer many rules of the form: :~ L1. [WEIGHT]
        """

        number_literals = symbols[2]
        number_negative_literals = symbols[3]
        literals_offset = 4
        weights_offset = literals_offset + number_literals

        for literal_index in range(number_literals):

            symbol = symbols[literal_index + literals_offset]
            weight = symbols[literal_index + weights_offset]
            
            literal = self.infer_symbol_name(symbol, insert_flags)

            if literal_index < number_negative_literals:
                signum_string = "not "
            else:
                signum_string = ""

            parsed_rules.append(f":~ {signum_string}{literal}. [{weight},{self.global_weight_index}]")
            self.global_weight_index += 1

    def handle_smodels_disjunctive_head_rule(self, symbols, insert_flags):
        """
        -- Handle smodels disjunctive rule with type 8:
        SYNAPSIS: 8 #hlits heads #literals #negative negative positive
        """

        heads = symbols[1]

        heads_list = []
        head_string_index = 2

        for head_index in range(heads):

            head_string_index = 2 + head_index

            head_symbol = symbols[head_string_index]

            heads_list.append(self.infer_symbol_name(head_symbol, insert_flags))

        head_string = "|".join(heads_list)

        body_start_string_index = head_string_index + 1

        number_body_literals = symbols[body_start_string_index]
        number_negative_body_literals = symbols[body_start_string_index + 1]

        if number_body_literals == 0:
            return head_string + "."
        else:

            body_string_list = []
            remaining_body_literals = symbols[body_start_string_index + 2:]

            for body_symbol in remaining_body_literals:

                body_literal = self.infer_symbol_name(body_symbol, insert_flags)

                if len(body_string_list) < number_negative_body_literals:
                    body_string_list.append("not " + body_literal)
                else:
                    body_string_list.append(body_literal)


            body = ",".join(body_string_list)

            return head_string + " :- " + body + "."

    def infer_symbol_name(self, symbol, insert_flags):
        if symbol in self.literals_dict:
            
            if insert_flags is False:
                # Normal Case
                return self.literals_dict[symbol]
            else:
                # Final Print Case (re-insert #sup and #inf)
                literal = self.literals_dict[symbol]
                if self.sup_flag in literal:
                    literal = literal.replace(self.sup_flag, "#sup")
                
                if self.inf_flag in literal:
                    literal = literal.replace(self.inf_flag, "#inf")

                return literal
        else:
            return self.auxiliary_name + str(symbol)





        









            
