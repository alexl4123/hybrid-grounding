import itertools

import clingo.propagator as clingo_propagator

from heuristic_splitter.cdnl.cdnl_data_structure import CDNLDataStructure

class BDGPropagator:

    def __init__(self, cdnl_data_structure: CDNLDataStructure):

        self.cdnl_data_structure = cdnl_data_structure

        self.literal_symbol_mapper = {}
        self.symbol_literal_mapper = {}
        self.rule_has_added_literals = {}

        self.queue_added_nogoods = []

    def init(self, init):
        init.check_mode = clingo_propagator.PropagatorCheckMode.Both
        print(f"Number of Threads: {init.number_of_threads}")

        for atom in init.symbolic_atoms:
            
            literal = init.solver_literal(atom.literal)
            init.add_watch(literal)

            atom_symbol = atom.symbol
            
            if atom_symbol.name not in self.symbol_literal_mapper:
                self.symbol_literal_mapper[atom_symbol.name] = {}
                self.symbol_literal_mapper[atom_symbol.name]["grounded_symbols"] = {}
            
            self.symbol_literal_mapper[atom_symbol.name]["grounded_symbols"][str(atom_symbol)] = literal

            atom_object = {}
            atom_object["name"] = atom_symbol.name
            atom_object["signum_is_positive"] = atom_symbol.positive

            arguments = []
            for argument in atom_symbol.arguments:
                arguments.append(str(argument))

            atom_object["terms"] = arguments

            if literal not in self.literal_symbol_mapper:
                self.literal_symbol_mapper[literal] = []

            self.literal_symbol_mapper[literal].append(atom_object)

        for theory_atom in init.theory_atoms:
            print(theory_atom.symbol)

    def propagate(self, control, changes):
        if len(self.queue_added_nogoods) > 0:
            ret_val = True
            while ret_val is True:
                ret_val = control.add_nogood(self.queue_added_nogoods[len(self.queue_added_nogoods) - 1], lock=True)
                self.queue_added_nogoods.pop(len(self.queue_added_nogoods) - 1)
                ret_val = ret_val and control.propagate()

                if len(self.queue_added_nogoods) == 0:
                    break
            return


    def undo(self, thread_id, assignment, changes):
        #print("CDNL-UNDO")
        pass

    def check(self, control):

        if len(self.queue_added_nogoods) > 0:
            ret_val = True
            while ret_val is True:
                ret_val = control.add_nogood(self.queue_added_nogoods[len(self.queue_added_nogoods) - 1], lock=True)
                self.queue_added_nogoods.pop(len(self.queue_added_nogoods) - 1)
                ret_val = ret_val and control.propagate()

                if len(self.queue_added_nogoods) == 0:
                    break
            return

        print("CDNL-CHECK")

        assignment = control.assignment

        foundedness_check_necessary = {}
        positive_symbol_structure = {}

        for literal in assignment:
            if literal in self.literal_symbol_mapper:
                symbol_list = self.literal_symbol_mapper[literal]
                if assignment.is_true(literal):

                    for symbol in symbol_list:
                        symbol_name = symbol["name"]


                        if symbol_name in self.cdnl_data_structure.bdg_literals:
                            scc_index = self.cdnl_data_structure.graph_ds.positive_predicate_scc_index[symbol_name]
                            scc = self.cdnl_data_structure.graph_ds.positive_sccs[scc_index]
                            if len(scc) > 1:
                                # TODO -> Infer foundedness check!
                                print(f"NON TRIVIAL SCC FOR {symbol_name}")
                                foundedness_check_necessary[str(symbol)] = (literal, symbol)

                        if symbol_name not in positive_symbol_structure:
                            positive_symbol_structure[symbol_name] = {}
                            positive_symbol_structure[symbol_name]["terms"] = {}

                        positive_symbol_structure[symbol_name]["terms"][str(symbol["terms"])] = literal

                #for symbol in symbol_list:
                #    print(f"literal:{literal}, symbol:{symbol}, true: {assignment.is_true(literal)}")
 
        if len(foundedness_check_necessary) > 0:

            unfound_set, external_body_set = self.unfound_set_algorithm(foundedness_check_necessary, positive_symbol_structure, control)

            if len(unfound_set) > 0 and len(external_body_set) > 0:

                external_literals = []
                for atom_name in external_body_set:
                    for terms in external_body_set[atom_name]:

                        parsed_terms = []
                        for term in terms[1:-1].split(","):
                            parsed_terms.append(term[1:-1])

                        literal_string = atom_name + "(" + ",".join(parsed_terms) + ")"
                        literal = self.symbol_literal_mapper[atom_name]["grounded_symbols"][literal_string]
                        external_literals.append(-literal)

                for unfound_atom_name in unfound_set:
                    for unfound_term_name in unfound_set[unfound_atom_name]:

                        parsed_terms = []
                        for term in unfound_term_name[1:-1].split(","):
                            parsed_terms.append(term[1:-1])

                        literal_string = unfound_atom_name + "(" + ",".join(parsed_terms) + ")"
                        literal = self.symbol_literal_mapper[unfound_atom_name]["grounded_symbols"][literal_string]

                        nogood = [literal] + external_literals

                        self.queue_added_nogoods.append(nogood)





    def unfound_set_algorithm(self, foundedness_check_necessary, positive_symbol_structure, control):

        support_checked_set = {}

        for key in foundedness_check_necessary.keys():

            # Initialize U = {p}
            unfound_set = {}
            unfound_set[foundedness_check_necessary[key][1]['name']] = {}
            unfound_set[foundedness_check_necessary[key][1]['name']][str(foundedness_check_necessary[key][1]["terms"])] = True

            unfound_semi_set = {}
            
            # repeat
            while len(unfound_set) > 0:

                tmp_external_body_set = {}


                # -----
                # Infer \beta \in EB_{\Pi}(U)
                positive_predecessors = {}

                for unfound_key in unfound_set.keys():

                    symbol_name = unfound_key
                    symbol = {"name": symbol_name}

                    for term_key in unfound_set[unfound_key].keys():

                        graph_symbol_index = self.cdnl_data_structure.graph_ds.predicate_to_index_lookup[symbol_name]

                        # Infering EB_{\Pi}(U):
                        predecessors = self.cdnl_data_structure.graph_ds.positive_graph.predecessors(graph_symbol_index)


                        for predecessor_graph_index in list(predecessors):

                            predecessor_atom = self.cdnl_data_structure.graph_ds.index_to_predicate_lookup[predecessor_graph_index]

                            if predecessor_atom in unfound_semi_set and term_key in unfound_semi_set[predecessor_atom]:
                                print(f"--> {predecessor_atom} already handled --> Skipping")
                                continue

                            print(predecessor_atom)
                            if predecessor_atom not in tmp_external_body_set:
                                tmp_external_body_set[predecessor_atom] = {}
                            if term_key not in tmp_external_body_set[predecessor_atom]:
                                tmp_external_body_set[predecessor_atom][term_key] = True

                            if predecessor_atom in positive_symbol_structure and term_key in positive_symbol_structure[predecessor_atom]["terms"]:

                                if predecessor_atom not in positive_predecessors:
                                    positive_predecessors[predecessor_atom] = {}

                                positive_predecessors[predecessor_atom][term_key] = term_key

                # if EB_{\Pi}(U) \subseteq A^F then return U
                if len(positive_predecessors) == 0:
                    print("return U --> TODO!")
                    print(tmp_external_body_set)
                    return unfound_set, tmp_external_body_set
                # -----


                for positive_predecessor_key in positive_predecessors.keys():

                    # Find body to positive_predecessor_key (HEAD)
                    # Check SCC and support checked!

                    self.find_positive_body(symbol, positive_predecessor_key, positive_predecessors, positive_symbol_structure, support_checked_set, unfound_set, unfound_semi_set)

        return {}, {}


    def find_positive_body(self, symbol, positive_predecessor_key, positive_predecessors, positive_symbol_structure, support_checked_set, unfound_set, unfound_semi_set):


        #terms = positive_predecessors[positive_predecessor_key]
        # Find Rule:
        graph_index = self.cdnl_data_structure.graph_ds.predicate_to_index_lookup[positive_predecessor_key]
        rule_index = self.cdnl_data_structure.graph_ds.node_to_rule_lookup[graph_index]
        rule = self.cdnl_data_structure.rule_dictionary[rule_index[0]]

        head_literal = None
        for literal in rule.literals:
            if "FUNCTION" in literal and literal["FUNCTION"].in_head is True:
                head_literal = literal["FUNCTION"]
                break

        for head_terms in positive_predecessors[positive_predecessor_key].keys():
            variable_assignments = {}
            for argument_index in range(len(head_literal.arguments)):
                if "VARIABLE" in head_literal.arguments[argument_index]:
                    variable_name = head_literal.arguments[argument_index]["VARIABLE"]
                    value = positive_predecessors[positive_predecessor_key][head_terms][1:-1].split(",")[argument_index][1:-1]
                    variable_assignments[variable_name] = value


            worked, body_assignment = self.join_helper(variable_assignments, rule, 0, positive_symbol_structure)

            if worked is True:

                head_scc_index = self.cdnl_data_structure.graph_ds.positive_predicate_scc_index[head_literal.name]

                not_handled_literals = []
                for assignment in body_assignment:
                    body_literal_scc_index = self.cdnl_data_structure.graph_ds.positive_predicate_scc_index[assignment["name"]]

                    if body_literal_scc_index != head_scc_index:
                        continue
                    elif body_literal_scc_index == head_scc_index:
                        assignment_term = str(list(assignment["term"].keys())[0])
                        if assignment["name"] in support_checked_set:
                            if assignment_term in support_checked_set[assignment["name"]]:
                                continue

                        if assignment["name"] not in unfound_set:
                            unfound_set[assignment["name"]] = {}
                        
                        if assignment_term not in unfound_set[assignment["name"]]:
                            unfound_set[assignment["name"]][assignment_term] = True

                        not_handled_literals.append(assignment)

                        if positive_predecessor_key not in unfound_semi_set:
                            unfound_semi_set[positive_predecessor_key] = {}
                        if head_terms not in unfound_semi_set[positive_predecessor_key]:
                            unfound_semi_set[positive_predecessor_key][head_terms] = True

                if len(not_handled_literals) == 0:
                    # We found support:
                    # U := U \ {q} (and q_1 - this is predecessor key)
                    # S := S \ {q} (...)
                    # UNIVERSE \ S = support_checked_set (so inverse)
                    # U = unfound_set

                    if positive_predecessor_key not in support_checked_set:
                        support_checked_set[positive_predecessor_key] = {}
                    if head_terms not in support_checked_set[positive_predecessor_key]:
                        support_checked_set[positive_predecessor_key][head_terms] = True

                    if positive_predecessor_key in unfound_set:
                        if head_terms in unfound_set[positive_predecessor_key]:
                            del unfound_set[positive_predecessor_key][head_terms]

                        if len(unfound_set[symbol["name"]]) == 0:
                            del unfound_set[positive_predecessor_key]

                    if symbol["name"] not in support_checked_set:
                        support_checked_set[symbol["name"]] = {}
                    if head_terms not in support_checked_set[symbol["name"]]:
                        support_checked_set[symbol["name"]][head_terms] = True

                    
                    if symbol["name"] in unfound_set:
                        if head_terms in unfound_set[symbol["name"]]:
                            del unfound_set[symbol["name"]][head_terms]

                        if len(unfound_set[symbol["name"]]) == 0:
                            del unfound_set[symbol["name"]]











        print(str(rule))

    def join_helper(self, variable_assignments, rule, literals_index, positive_symbol_structure):
        """
        Tries to find a matching positive body.
        --> This is done via joins.
        """


        if literals_index >= len(rule.literals):
            # Base Case of Recursive Function
            return True, []

        assignments = []
        worked = False

        if "FUNCTION" in rule.literals[literals_index]:
            function = rule.literals[literals_index]["FUNCTION"]
            
            if function.in_head is False and function.signum > 0:

                print(function)

                if function.name not in positive_symbol_structure:
                    return False, []

                terms = positive_symbol_structure[function.name]["terms"]

                positive_assignment = None

                for term in terms.keys():

                    term_values = term[1:-1].split(",")
                    tmp_variable_assignments = {}

                    assignment_found = True

                    # Check if matches variable assignments:
                    for argument_index in range(len(term_values)):

                        term_value = term_values[argument_index]

                        # As term_value is a double string ("'1'" and not '1')
                        term_value = term_value[1:-1]
                        non_ground_function_argument = function.arguments[argument_index]

                        if "VARIABLE" in non_ground_function_argument:

                            variable_name = non_ground_function_argument["VARIABLE"]

                            if variable_name in variable_assignments:
                                variable_value = variable_assignments[variable_name]
                                if variable_value != term_value:
                                    assignment_found = False
                                    break
                            elif variable_name in tmp_variable_assignments:
                                variable_value = variable_assignments[variable_name]
                                if variable_value != term_value:
                                    tmp_variable_assignments.clear()
                                    assignment_found = False
                                    break
                            else:
                                tmp_variable_assignments[variable_name] = term_value
                        else:
                            raise NotImplementedError("Not Implemented")

                    if assignment_found is True:
                        new_variable_assignments = variable_assignments | tmp_variable_assignments
                        worked, assignments = self.join_helper(new_variable_assignments, rule, literals_index + 1, positive_symbol_structure)

                        if worked is True:
                            assignments.append({'name': function.name, 'term': {term:terms[term]}})
                            return worked, assignments

            else:
                worked, assignments = self.join_helper(variable_assignments, rule, literals_index + 1, positive_symbol_structure)
                return worked, assignments
            
        else:
            raise NotImplementedError("Not yet implemented ...")

        return worked, assignments



    




            
            
                    
                    


            


        

        




