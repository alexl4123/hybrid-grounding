# pylint: disable=R1705,W0108,R1703
"""
The MiscTools module is a toolbox for various ''check'' methods.
"""

import re


class MiscTools:
    """
    The MiscTools class is a toolbox for various ''check'' methods.
    """

    variable_regex = re.compile(r"_*[A-Z][A-Za-z0-9_’]*")

    @classmethod
    def string_is_variable(cls, string):
        """
        Checks a given string,
        if it is a variable according to ASP Syntax.
        """

        ret = cls.variable_regex.match(string)

        if ret is not None:
            return True
        else:
            return False
