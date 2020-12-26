from llvmAnalyser.llvmChecker import *
from llvmAnalyser.function import Parameter as Argument
from llvmAnalyser.types import get_type
from llvmAnalyser.values import get_value
from llvmAnalyser.llvmStatement import LlvmStatement
from llvmAnalyser.conversion.conversion import analyze_conversion


# The ‘call’ instruction represents a simple function call.

# <result> = [tail | musttail | notail ] call [fast-math flags] [cconv] [ret attrs] [addrspace(<num>)]
#            <ty>|<fnty> <fnptrval>(<function args>) [fn attrs] [ operand bundles ]


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
        attr = tokens.pop(0)
        if attr == "cc":
            attr += " {}".format(tokens.pop(0))
        call.set_calling_convention(attr)
    else:
        call.set_calling_convention("ccc")

    # check if there are parameter attributes
    while is_parameter_attribute(tokens[0]):
        open_brackets = tokens[0].count("(") - tokens[0].count(")")
        attr = tokens.pop(0)
        while open_brackets != 0:
            open_brackets += tokens[0].count("(") - tokens[0].count(")")
            attr += " {}".format(tokens.pop(0))
        call.add_return_attr(attr)

    # skip the return type
    temp_type, tokens = get_type(tokens)

    # skip potential redundant tokens
    while tokens[0].count("(") == 0 and "bitcast" not in tokens[0]:
        tokens.pop(0)

    # read the function name
    if "bitcast" in tokens[0]:
        conversion = analyze_conversion(tokens)
        call.set_function_name(conversion.get_value())
        if tokens[0][0] == "(":
            tokens[0] = tokens[0][1:]
    else:
        temp = tokens[0].split("(", 1)
        tokens[0] = temp[1]

        call.set_function_name(temp[0])

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
                attribute += " {}".format(tokens.pop(0))
            argument.add_parameter_attribute(attribute)

        # read register
        value, tokens = get_value(tokens)
        argument.set_register(value)

        call.add_argument(argument)

    # make sure you finish the parameter list, this token will not get popped if we have an empty argument list
    if tokens and tokens[0] == ")":
        tokens.pop(0)

    # read function attributes
    if tokens and is_group_attribute(tokens[0]):
        call.set_group_function_attribute(tokens[0])
        tokens.pop(0)
    while tokens and is_function_attribute(tokens[0]):
        if "allocsize" in tokens[0]:
            attribute = tokens.pop(0)
            open_brackets = attribute.count("(") - attribute.count(")")
            while open_brackets != 0:
                open_brackets += tokens[0].count("(") - tokens[0].count(")")
                attribute += " {}".format(tokens.pop(0))
            call.add_function_attribute(attribute)
        else:
            call.add_function_attribute(tokens.pop(0))

    # analyze operand bundle sets
    if tokens and "[" in tokens[0]:
        operand_bundle_set = OperandBundleSet()
        tokens.pop(0)

        # analyze operand bundles
        while tokens[0] != "]":
            operand_bundle = OperandBundle()

            # get the operand bundle tag
            quote_count = tokens[0].count("\"")
            tag = tokens.pop(0)
            while quote_count < 2:
                tag += " {}".format(tokens.pop(0))
                quote_count = tag.count("\"")

            temp = tag.split('"', 2)
            operand_bundle.set_tag("\"{}\"".format(temp[1]))
            tokens.insert(0, temp[-1])

            desired_remaining_token_length = get_nr_of_tokens_past_last_bracket(tokens)

            if tokens[0][0] == ")":
                operand_bundle_set.add_operand_bundle(operand_bundle)
                tokens.pop(0)
                continue

            # analyze operands
            while len(tokens) > desired_remaining_token_length:
                operand = Operand()

                operand_type, tokens = get_type(tokens)
                operand.set_type(operand_type)

                operand_value, tokens = get_value(tokens)
                operand.set_value(operand_value)

                operand_bundle.add_operand(operand)

            operand_bundle_set.add_operand_bundle(operand_bundle)

        call.set_operand_bundle_set(operand_bundle_set)

        tokens.pop(0)

    return call


def get_nr_of_tokens_past_last_bracket(tokens):
    tokens[0] = tokens[0][1:]

    open_brackets = 1

    # loop over the tokens until this first bracket is closed again, when this happens, return the index
    for i in range(len(tokens)):
        for j in range(len(tokens[i])):
            char = tokens[i][j]
            if char == "(":
                open_brackets += 1
            elif char == ")":
                open_brackets -= 1
            if open_brackets == 0:
                return len(tokens) - i


class Call(LlvmStatement):
    def __init__(self):
        super().__init__()
        self.function_name = None
        self.arguments = list()
        self.function_attributes = list()
        self.operand_bundle_set = None
        self.memory = None
        self.calling_convention = None
        self.return_attrs = list()

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

    def get_function_attributes(self):
        return self.function_attributes

    def set_operand_bundle_set(self, op_set):
        self.operand_bundle_set = op_set

    def get_operand_bundle_set(self):
        return self.operand_bundle_set

    def get_used_variables(self):
        variable_values = list()
        for argument in self.arguments:
            variable_values.append(argument.get_register())
        return variable_values

    def set_calling_convention(self, cconv):
        self.calling_convention = cconv

    def get_calling_convention(self):
        return self.calling_convention

    def add_return_attr(self, attr):
        self.return_attrs.append(attr)

    def get_return_attrs(self):
        return self.return_attrs

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


class OperandBundleSet:
    def __init__(self):
        self.operand_bundles = list()

    def add_operand_bundle(self, bundle):
        self.operand_bundles.append(bundle)

    def get_operand_bundles(self):
        return self.operand_bundles


class OperandBundle:
    def __init__(self):
        self.tag = None
        self.operands = list()

    def set_tag(self, tag):
        self.tag = tag

    def get_tag(self):
        return self.tag

    def add_operand(self, operand):
        self.operands.append(operand)

    def get_operands(self):
        return self.operands


class Operand:
    def __init__(self):
        self.operand_type = None
        self.operand_value = None

    def set_value(self, operand_value):
        self.operand_value = operand_value

    def get_value(self):
        return self.operand_value

    def set_type(self, operand_type):
        self.operand_type = operand_type

    def get_type(self):
        return self.operand_type
