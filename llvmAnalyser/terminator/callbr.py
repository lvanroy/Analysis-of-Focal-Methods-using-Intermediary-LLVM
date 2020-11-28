from llvmAnalyser.llvmStatement import LlvmStatement
from llvmAnalyser.llvmchecker import is_calling_convention, is_parameter_attribute, is_address_space, \
    is_function_attribute
from llvmAnalyser.types import get_type
from llvmAnalyser.values import get_value


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
        tokens.pop(0)

    # pop the address space
    if is_address_space(tokens[0]):
        tokens.pop(0)

    # get the return type
    ret_type, tokens = get_type(tokens)
    br.set_return_type(ret_type)

    while "(" not in tokens[0]:
        tokens.pop(0)

    # get the function name
    br.set_function(tokens[0].split("(")[0])
    tokens[0] = tokens[0].split("(")[1]

    while "(" in tokens[0] or ")" not in tokens[0]:
        argument = Argument()

        # get the arg type
        arg_type, tokens = get_type(tokens)
        argument.set_argument_type(arg_type)

        # read potential parameter attributes
        while is_parameter_attribute(tokens[0]):
            tokens.pop(0)

        # read the parameter value
        value, tokens = get_value(tokens)
        argument.set_argument_name(value)
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

    def set_fallthrough_label(self, fallthrough_label):
        self.fallthrough_label = fallthrough_label

    def get_fallthrough_label(self):
        return self.fallthrough_label

    def add_indirect_label(self, label):
        self.indirect_labels.append(label)

    def get_indirect_label(self):
        return self.indirect_labels


class Argument:
    def __init__(self):
        self.argument_type = None
        self.argument_name = None

    def set_argument_type(self, argument_type):
        self.argument_type = argument_type

    def get_argument_type(self):
        return self.argument_type

    def set_argument_name(self, argument_name):
        self.argument_name = argument_name

    def get_argument_name(self):
        return self.argument_name
