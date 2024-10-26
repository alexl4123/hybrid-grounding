
from heuristic_splitter.domain_inferer import DomainInferer
from heuristic_splitter.program.asp_program import ASPProgram

class SmodelsASPProgram(ASPProgram):

    def __init__(self, grd_call, debug_mode = False):

        self.program = []
        self.literals_dict = {}
        self.debug_mode = debug_mode

        self.other_prg_string = ""

        self.auxiliary_name = f"auxiliary_{grd_call}_"


    def preprocess_smodels_program(self, smodels_program_string, domain_inferer: DomainInferer):

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

                self.literals_dict[symbol] = literal

                domain_inferer.parse_smodels_literal(literal)
            else:
                continue

    def add_string(self, to_add_prg):
        """
        To handle compability with NaGG (NaGG output is string).
        """

        self.other_prg_string = self.other_prg_string + to_add_prg

    def get_string(self):

        if self.debug_mode is True:
            print("+++++ START REWRITING SMODELS OUTPUT +++++")

        parsed_rules = []
        for rule in self.program:
            if self.debug_mode is True:
                print(rule)
            if rule[0] == '1':
                parsed_rule = self.handle_normal_rule(rule)
                if self.debug_mode is True:
                    print(parsed_rule)
                parsed_rules.append(parsed_rule)
            elif rule[0] == '2':
                parsed_rule = self.handle_smodels_constraint_rule(rule)
                if self.debug_mode is True:
                    print(parsed_rule)
                parsed_rules.append(parsed_rule)
            elif rule[0] == '3':
                parsed_rule = self.handle_smodels_choice_rule(rule)
                if self.debug_mode is True:
                    print(parsed_rule)
                parsed_rules.append(parsed_rule)
            elif rule[0] == '4': 
                raise Exception("Was never defined!")
            elif rule[0] == '5':
                parsed_rule = self.handle_smodels_weight_rule(rule)
                if self.debug_mode is True:
                    print(parsed_rule)
                parsed_rules.append(parsed_rule)
            elif rule[0] == '8':
                parsed_rule = self.handle_smodels_disjunctive_head_rule(rule)
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

        return "\n".join(parsed_rules) + self.other_prg_string

    def handle_normal_rule(self, rule):
        """
        -- Handle smodels rule with type 1:
        SYNAPSIS: 1 head #literals #negative negative positive
        """

        symbols = rule.split(" ")

        head_symbol = symbols[1]

        number_body_literals = int(symbols[2])
        number_negative_body_literals = int(symbols[3])

        if number_body_literals == 0:
            return self.infer_symbol_name(head_symbol) + "."
        else:
            head = self.infer_symbol_name(head_symbol)

            body_string_list = []
            remaining_body_literals = symbols[4:]

            for body_symbol in remaining_body_literals:

                body_literal = self.infer_symbol_name(body_symbol)

                if len(body_string_list) < number_negative_body_literals:
                    body_string_list.append("not " + body_literal)
                else:
                    body_string_list.append(body_literal)


            body = ",".join(body_string_list)

            return head + " :- " + body + "."

    def handle_smodels_constraint_rule(self, rule):
        """
        -- Handle an SMODELS constraint rule (not an ASP constraint)
        SYNAPSIS: 2 head #literals #negative bound negative positive
        CORRESPONDS TO: head :- bound <= #count{literal0; literal1; ...}
        OR SIMPLIFIED: head :- bound {literal0; literal1; ...}
        """

        symbols = rule.split(" ")
        head_symbol = symbols[1]

        number_body_literals = int(symbols[2])
        number_negative_body_literals = int(symbols[3])
        bound = int(symbols[4])

        if number_body_literals == 0:
            return self.infer_symbol_name(head_symbol) + "."
        else:
            head = self.infer_symbol_name(head_symbol)

            body_string_list = []
            remaining_body_literals = symbols[5:]

            for body_symbol in remaining_body_literals:

                body_literal = self.infer_symbol_name(body_symbol)

                if len(body_string_list) < number_negative_body_literals:
                    body_string_list.append("not " + body_literal)
                else:
                    body_string_list.append(body_literal)


            body = ";".join([f"1,{index}:{body_string_list[index]}" for index in range(len(body_string_list))])

            return head + " :- " + str(bound) + " <= #count{" + body + "}."

    
    def handle_smodels_choice_rule(self, rule):
        """
        -- Handle an SMODELS choice rule
        SYNAPSIS: 3 #heads heads #literals #negative negative positive
        CORRESPONDS TO: {heads} :- body 
        """

        symbols = rule.split(" ")
        heads = int(symbols[1])

        heads_list = []
        head_string_index = 2

        for head_index in range(heads):

            head_string_index = 2 + head_index

            head_symbol = symbols[head_string_index]

            heads_list.append(self.infer_symbol_name(head_symbol))

        
        head_string = "{" + ";".join(heads_list) + "}"

        body_start_string_index = head_string_index + 1

        number_body_literals = int(symbols[body_start_string_index])
        number_negative_body_literals = int(symbols[body_start_string_index + 1])

        if number_body_literals == 0:
            return head_string + "."
        else:

            body_string_list = []
            remaining_body_literals = symbols[body_start_string_index + 2:]

            for body_symbol in remaining_body_literals:

                body_literal = self.infer_symbol_name(body_symbol)

                if len(body_string_list) < number_negative_body_literals:
                    body_string_list.append("not " + body_literal)
                else:
                    body_string_list.append(body_literal)


            body = ",".join(body_string_list)

            return head_string + " :- " + body + "."


    def handle_smodels_weight_rule(self, rule):
        """
        -- Handle SMODELS weight rule.
        SYNPOSIS: 5 head bound #lits #negative negative positive weights
        """

        symbols = rule.split(" ")
        head_symbol = symbols[1]
        bound = int(symbols[2])
        number_body_literals = int(symbols[3])
        number_negative_body_literals = int(symbols[4])

        if number_body_literals == 0:
            return self.infer_symbol_name(head_symbol) + "."
        else:
            head = self.infer_symbol_name(head_symbol)

            body_string_list = []
            remaining_body_literals = symbols[5:]

            for body_symbol_index in range(number_body_literals):

                body_symbol = remaining_body_literals[body_symbol_index]
                body_literal = self.infer_symbol_name(body_symbol)

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

    def handle_smodels_disjunctive_head_rule(self, rule):
        """
        -- Handle smodels disjunctive rule with type 8:
        SYNAPSIS: 8 #hlits heads #literals #negative negative positive
        """

        symbols = rule.split(" ")

        heads = int(symbols[1])

        heads_list = []
        head_string_index = 2

        for head_index in range(heads):

            head_string_index = 2 + head_index

            head_symbol = symbols[head_string_index]

            heads_list.append(self.infer_symbol_name(head_symbol))

        head_string = "|".join(heads_list)

        body_start_string_index = head_string_index + 1

        number_body_literals = int(symbols[body_start_string_index])
        number_negative_body_literals = int(symbols[body_start_string_index + 1])

        if number_body_literals == 0:
            return head_string + "."
        else:

            body_string_list = []
            remaining_body_literals = symbols[body_start_string_index + 2:]

            for body_symbol in remaining_body_literals:

                body_literal = self.infer_symbol_name(body_symbol)

                if len(body_string_list) < number_negative_body_literals:
                    body_string_list.append("not " + body_literal)
                else:
                    body_string_list.append(body_literal)


            body = ",".join(body_string_list)

            return head_string + " :- " + body + "."

    def infer_symbol_name(self, symbol):
        if symbol in self.literals_dict:
            return self.literals_dict[symbol]
        else:
            return self.auxiliary_name + symbol





        









            
