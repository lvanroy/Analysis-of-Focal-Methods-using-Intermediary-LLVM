from llvmAnalyser.llvmchecker import *
from llvmAnalyser.function import Parameter as Argument


class CallAnalyzer:
    def __init__(self):
        pass

    @staticmethod
    def analyze_call(tokens):
        i = 0
        call = Call()

        # skip all initial tokens
        while tokens[i] != "call":
            i += 1

        i += 1

        # check if there are fast-math flags
        while is_fast_math_flag(tokens[i]):
            i += 1

        # check if there is a cconv field
        if is_calling_convention(tokens[i]):
            i += 1

        # check if there are parameter attributes
        while is_parameter_attribute(tokens[i]):
            i += 1

        # skip the return type
        i += 1
        if tokens[i] in {"()", "()*"}:
            i += 1

        # read the function name
        temp = tokens[i].split("(")
        tokens[i] = temp[0]
        tokens.insert(i + 1, temp[1])

        call.set_function_name(tokens[i])
        i += 1

        # read the argument list
        while "(" in tokens[i] or ")" not in tokens[i]:
            argument = Argument()

            # read argument type
            if tokens[i + 1] in {"()", "()*"}:
                argument.set_parameter_type("{} {}".format(tokens[i], tokens[i + 1]))
                i += 2
            else:
                argument.set_parameter_type(tokens[i])
                i += 1

            # read potential parameter attributes
            while is_parameter_attribute(tokens[i]):
                argument.add_parameter_attribute(tokens[i])
                i += 1

            # read register
            argument.set_register(tokens[i].replace(")", "").replace(",", ""))

            call.add_argument(argument)

        i += 1

        if i < len(tokens) and is_group_attribute(tokens[i]):
            call.set_group_function_attribute(tokens[i])
            i += 1
        else:
            while i < len(tokens) and is_function_attribute(tokens[i]):
                call.add_function_attribute(tokens[i])
                i += 1

        return call


class Call:
    def __init__(self):
        self.function_name = None
        self.arguments = list()
        self.function_attributes = list()

    def set_function_name(self, function_name):
        self.function_name = function_name

    def add_argument(self, argument):
        self.arguments.append(argument)

    def set_group_function_attribute(self, group_attribute):
        self.function_attributes = group_attribute

    def add_function_attribute(self, function_attribute):
        self.function_attributes.append(function_attribute)

    def get_function_name(self):
        return self.function_name

    def __str__(self):
        output = "call {}(".format(self.function_name)
        for argument in self.arguments:
            output += "{}, ".format(argument)
        output += ") "

        if type(self.function_attributes) == list:
            for func_attr in self.function_attributes:
                output += "{} ".format(func_attr)
        else:
            output += self.function_attributes
        return output
