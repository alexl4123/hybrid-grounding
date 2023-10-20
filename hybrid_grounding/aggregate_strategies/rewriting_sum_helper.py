import itertools

import clingo

from ..comparison_tools import ComparisonTools
from .aggregate_mode import AggregateMode
from .count_aggregate_helper import CountAggregateHelper
from .rs_helper import RSHelper
from .rs_plus_star_helper import RSPlusStarHelper


class RewritingSumHelper:
    @classmethod
    def rs_sum_generate_alldiff_rules_helper(
        cls,
        rule_head_name,
        sum,
        elements,
        str_type,
        str_id,
        variable_dependencies,
        aggregate_mode,
        cur_variable_dependencies,
        always_add_variable_dependencies,
        skolem_constants,
    ):
        rules_strings = []

        for secondary_guard_value in range(1, sum + 1):
            tmp_rules_strings = RSHelper._rs_count_generate_count_rule(
                rule_head_name,
                secondary_guard_value,
                elements,
                str_type,
                str_id,
                variable_dependencies,
                aggregate_mode,
                cur_variable_dependencies,
                always_add_variable_dependencies,
                skolem_constants,
                total_count=sum,
            )

            rules_strings += tmp_rules_strings

        return rules_strings

    @classmethod
    def rs_plus_star_sum_generate_alldiff_rules_helper(
        cls,
        rule_head_name,
        sum,
        elements,
        str_type,
        str_id,
        variable_dependencies,
        aggregate_mode,
        cur_variable_dependencies,
        always_add_variable_dependencies,
    ):
        rules_strings = []
        rules_head_strings = []

        for secondary_guard_value in range(1, sum + 1):
            (
                tmp_rules_strings,
                tmp_rules_head_strings,
            ) = RSPlusStarHelper._rs_plus_star_generate_all_diff_rules(
                rule_head_name,
                secondary_guard_value,
                elements,
                str_type,
                str_id,
                variable_dependencies,
                aggregate_mode,
                cur_variable_dependencies,
                always_add_variable_dependencies,
                sum,
            )

            rules_strings += tmp_rules_strings
            rules_head_strings += tmp_rules_head_strings

        if len(always_add_variable_dependencies) == 0:
            sum_name_ending = ""
            if len(variable_dependencies) == 0:
                sum_name_ending += "(1)"
            else:
                sum_name_ending += f"({','.join(variable_dependencies + always_add_variable_dependencies)})"
        else:
            sum_name_ending = f"({','.join(variable_dependencies + always_add_variable_dependencies)})"

        spawner_functions = []
        for variable in variable_dependencies:
            if variable in cur_variable_dependencies:
                cur_spawner_functions = cur_variable_dependencies[variable]
                for function in cur_spawner_functions:
                    spawner_functions.append(str(function))

        negated_head_strings = []
        for head_string in rules_head_strings:
            negated_head_strings.append(f"not {head_string}")

        helper_rule = f"not_{rule_head_name}{sum_name_ending} :- {','.join(spawner_functions + negated_head_strings)}."

        rules_strings.append(helper_rule)

        return rules_strings
