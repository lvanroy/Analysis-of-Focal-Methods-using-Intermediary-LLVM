from llvmAnalyser.llvmchecker import *


class InvokeAnalyzer:
    def __init__(self):
        pass

    @staticmethod
    def analyze_invoke(tokens):
        invoke = Invoke()

        # pop potential assignment
        while tokens[0] != "invoke":
            tokens.pop(0)

        tokens.pop(0)

        # pop calling convention
        if is_calling_convention(tokens[0]):
            tokens.pop(0)

        # pop optional return type attributes
        while is_parameter_attribute(tokens[0]):
            tokens.pop(0)

        # pop optional address space field
        if is_address_space(tokens[0]):
            tokens.pop(0)

        # pop return type
        tokens.pop(0)

        # get the function name
        invoke.set_func("invoke {}".format(tokens[0].split("(")[0]))

        bracket_count = tokens[0].count("(") - tokens[0].count(")")
        tokens.pop(0)
        while bracket_count != 0:
            bracket_count += tokens[0].count("(") - tokens[0].count(")")
            tokens.pop(0)

        # skip to the normal label
        while tokens[0] != "to":
            tokens.pop(0)
        tokens.pop(0)

        # pop label tag
        tokens.pop(0)

        invoke.set_normal(tokens[0].split("(")[0])
        tokens.pop(0)

        # pop "unwind label"
        tokens.pop(0)
        tokens.pop(0)
        invoke.set_exception(tokens[0].split("(")[0])

        return invoke


class Invoke:
    def __init__(self):
        self.func = None
        self.normal = None
        self.exception = None

    def set_func(self, func):
        self.func = func

    def get_func(self):
        return self.func

    def set_normal(self, normal):
        self.normal = normal

    def get_normal(self):
        return self.normal

    def set_exception(self, exception):
        self.exception = exception

    def get_exception(self):
        return self.exception
