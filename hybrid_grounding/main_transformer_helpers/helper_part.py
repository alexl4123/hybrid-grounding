# pylint: disable=W0102
"""
General helper module for the reduction.
"""


class HelperPart:
    """
    General helper class for the reduction.
    """

    @classmethod
    def get_domain_values_from_rule_variable(
        cls, rule, variable, domain, safe_variables_rules, rule_variables_predicates={}
    ):
        """
        Provided a rule number and a variable in that rule, one gets the domain of this variable.
        If applicable it automatically calculates the intersection of different domains.
        """

        if "0_terms" not in domain:
            # If no domain could be inferred
            raise Exception("A domain must exist when calling this method!")

        possible_domain_value_name = f"term_rule_{str(rule)}_variable_{str(variable)}"
        if possible_domain_value_name in domain:
            return domain[possible_domain_value_name]["0"]

        if len(rule_variables_predicates.keys()) > 0:
            if variable in rule_variables_predicates:
                respective_predicates = rule_variables_predicates[variable]
                total_domain = None

                total_domain = cls._get_variable_domain_from_occurrences(domain, respective_predicates, total_domain)

                if total_domain is not None:
                    return list(total_domain)

        return cls._get_alternative_domain(safe_variables_rules, rule, domain, variable)

    @classmethod
    def _get_alternative_domain(cls,safe_variables_rules, rule, domain, variable):

        if str(rule) not in safe_variables_rules:
            return domain["0_terms"]

        if str(variable) not in safe_variables_rules[str(rule)]:
            return domain["0_terms"]

        total_domain = None

        for domain_type in safe_variables_rules[str(rule)][str(variable)]:
            if domain_type["type"] == "function":
                domain_name = domain_type["name"]
                domain_position = domain_type["position"]

                if domain_name not in domain:
                    return domain["0_terms"]

                if domain_position not in domain[domain_name]:
                    return domain["0_terms"]

                cur_domain = domain[domain_name][domain_position]

                if total_domain:
                    total_domain = total_domain.intersection(set(cur_domain))
                else:
                    total_domain = set(cur_domain)

        if total_domain is None:
            return domain["0_terms"]

        return list(total_domain)

    @classmethod
    def _get_variable_domain_from_occurrences(cls, domain, respective_predicates, total_domain):
        for respective_predicate in respective_predicates:
            respective_predicate_name = respective_predicate[0].name
            respective_predicate_position = respective_predicate[1]

            if (
                        respective_predicate_name not in domain
                        or str(respective_predicate_position)
                        not in domain[respective_predicate_name]
                    ):
                continue

            cur_domain = domain[respective_predicate_name][
                        str(respective_predicate_position)
                    ]

            if total_domain:
                total_domain = total_domain.intersection(set(cur_domain))
            else:
                total_domain = set(cur_domain)
        return total_domain

    @classmethod
    def ignore_exception(cls, ignore_exception=Exception, default_value=None):
        """Decorator for ignoring exception from a function
        e.g.   @ignore_exception(DivideByZero)
        e.g.2. ignore_exception(DivideByZero)(Divide)(2/0)
        """

        def dec(function):
            def _dec(*args, **kwargs):
                try:
                    return function(*args, **kwargs)
                except ignore_exception:
                    return default_value

            return _dec

        return dec
