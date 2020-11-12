"""
This is a superclass that is supposed to be inherited by all statement instances
It defines functions assumed to be defined for all statements.
"""


class LlvmStatement:
    def __init__(self):
        pass

    def get_used_variables(self):
        return list()
