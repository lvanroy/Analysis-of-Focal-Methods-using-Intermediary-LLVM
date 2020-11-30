from llvmAnalyser.llvmchecker import *
from llvmAnalyser.function import Parameter as Argument
from llvmAnalyser.types import get_type
from llvmAnalyser.values import get_value
from llvmAnalyser.llvmStatement import LlvmStatement


class CallAnalyzer:
    def __init__(self):
        pass

    @staticmethod
    def analyze_call(tokens: list):
        call = Call()

        # skip all initial tokens
        while tokens[0] != "call":
            tokens.pop(0)

        tokens.pop(0)

        # check if there are fast-math flags
        while is_fast_math_flag(tokens[0]):
            tokens.pop(0)

        # check if there is a cconv field
        if is_calling_convention(tokens[0]):
            tokens.pop(0)

        # check if there are parameter attributes
        while is_parameter_attribute(tokens[0]):
            tokens.pop(0)

        # skip the return type
        temp_type, tokens = get_type(tokens)

        # skip potential redundant tokens
        while tokens[0].count("(") == 0:
            tokens.pop(0)

        # read the function name
        temp = tokens[0].split("(", 1)
        tokens[0] = temp[0]
        tokens.insert(1, temp[1])

        call.set_function_name(tokens[0])
        tokens.pop(0)

        # read the argument list
        while "(" in tokens[0] or ")" not in tokens[0]:
            argument = Argument()

            # read argument type
            parameter_type, tokens = get_type(tokens)
            argument.set_parameter_type(parameter_type)

            # read potential parameter attributes
            while is_parameter_attribute(tokens[0]):
                argument.add_parameter_attribute(tokens[0])
                tokens.pop(0)

            # read register
            value, tokens = get_value(tokens)
            argument.set_register(value)

            call.add_argument(argument)

        tokens.pop(0)

        if tokens and is_group_attribute(tokens[0]):
            call.set_group_function_attribute(tokens[0])
            tokens.pop(0)
        else:
            while tokens and is_function_attribute(tokens[0]):
                call.add_function_attribute(tokens[0])
                tokens.pop(0)

        return call


class Call(LlvmStatement):
    def __init__(self):
        super().__init__()
        self.function_name = None
        self.arguments = list()
        self.function_attributes = list()
        self.memory = None

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

    def get_arguments(self):
        return self.arguments

    def get_used_variables(self):
        return self.arguments

    def __str__(self):
        output = "call {}(".format(self.function_name)
        for argument in self.arguments:
            output += "{}, ".format(argument)
        output = output[:-2] + ") "

        if type(self.function_attributes) == list:
            for func_attr in self.function_attributes:
                output += "{} ".format(func_attr)
        else:
            output += self.function_attributes
        return output
