from llvmAnalyser.llvmStatement import LlvmStatement
from llvmAnalyser.llvmChecker import is_calling_convention, is_parameter_attribute, is_address_space, \
    is_function_attribute, is_group_attribute
from llvmAnalyser.function import Parameter as Argument
from llvmAnalyser.types import get_type
from llvmAnalyser.values import get_value
from llvmAnalyser.conversion.conversion import analyze_conversion


# analyzer for the callbr command that will be of the form given below
# this is used to implement a goto instruction
# <result> = callbr [cconv] [ret attrs] [addrspace(<num>)] <ty>|<fnty> <fnptrval>(<function args>) [fn attrs]
#                   [operand bundles] to label <fallthrough label> [indirect labels]


def analyze_callbr(tokens: list):
    br = CallBr()

    # pop the potential assignment
    while tokens[0] != "callbr":
        tokens.pop(0)

    # pop the callbr command
    tokens.pop(0)

    # pop the calling convention
    if is_calling_convention(tokens[0]):
        tokens.pop(0)

    # pop the parameter attributes
    while is_parameter_attribute(tokens[0]):
        open_brackets = tokens[0].count("(") - tokens[0].count(")")
        tokens.pop(0)
        while open_brackets != 0:
            open_brackets += tokens[0].count("(") - tokens[0].count(")")
            tokens.pop(0)

    # pop the address space
    if is_address_space(tokens[0]):
        tokens.pop(0)

    # get the return type
    ret_type, tokens = get_type(tokens)
    br.set_return_type(ret_type)

    # skip potential redundant tokens
    while tokens[0].count("(") == 0 and "bitcast" not in tokens[0]:
        tokens.pop(0)

    # get the function name
    if "bitcast" in tokens[0]:
        conversion = analyze_conversion(tokens)
        br.set_function(conversion.get_value())
    else:
        temp = tokens[0].split("(", 1)
        br.set_function(temp[0])
        tokens[0] = temp[1]

    # read the argument list
    while tokens and \
            not is_group_attribute(tokens[0]) and \
            not is_function_attribute(tokens[0]) and \
            ("(" in tokens[0] or ")" not in tokens[0]):
        argument = Argument()

        # read argument type
        parameter_type, tokens = get_type(tokens)
        argument.set_parameter_type(parameter_type)

        # read potential parameter attributes
        while is_parameter_attribute(tokens[0]):
            open_brackets = tokens[0].count("(") - tokens[0].count(")")
            attribute = tokens.pop(0)
            while open_brackets != 0 or attribute == "align":
                open_brackets += tokens[0].count("(") - tokens[0].count(")")
                attribute += tokens.pop(0)
            argument.add_parameter_attribute(attribute)

        # read register
        value, tokens = get_value(tokens)
        argument.set_register(value)

        br.add_function_argument(argument)

    # pop potential function attributes
    while is_function_attribute(tokens[0]):
        tokens.pop(0)

    # pop operand bundles
    while tokens[0] != "to":
        tokens.pop(0)

    tokens.pop(0)
    tokens.pop(0)

    # pop the fallthrough label
    br.set_fallthrough_label(tokens.pop(0))

    while tokens:
        # pop the label token
        tokens.pop(0)

        # pop the label specification
        br.add_indirect_label(tokens.pop(0).replace("]", ""))

    return br


class CallBr(LlvmStatement):
    def __init__(self):
        super().__init__()
        self.return_type = None
        self.function_name = None
        self.function_arguments = list()
        self.fallthrough_label = None
        self.indirect_labels = list()

    def set_return_type(self, return_type):
        self.return_type = return_type

    def get_return_type(self):
        return self.return_type

    def set_function(self, function_name):
        self.function_name = function_name

    def get_function_name(self):
        return self.function_name

    def add_function_argument(self, argument):
        self.function_arguments.append(argument)

    def get_function_arguments(self):
        return self.function_arguments

    def get_argument_registers(self):
        registers = list()
        for argument in self.function_arguments:
            registers.append(argument.get_register())
        return registers

    def set_fallthrough_label(self, fallthrough_label):
        self.fallthrough_label = fallthrough_label

    def get_fallthrough_label(self):
        return self.fallthrough_label

    def add_indirect_label(self, label):
        self.indirect_labels.append(label)

    def get_indirect_label(self):
        return self.indirect_labels

    def get_used_variables(self):
        variable_values = list()
        for argument in self.function_arguments:
            variable_values.append(argument.get_register())
        return variable_values
