from llvmAnalyser.llvmChecker import *
from llvmAnalyser.llvmStatement import LlvmStatement
from llvmAnalyser.function import Parameter as Argument
from llvmAnalyser.conversion.conversion import analyze_conversion
from llvmAnalyser.values import get_value
from llvmAnalyser.types import get_type


# The ‘invoke’ instruction causes control to transfer to a specified function,
# with the possibility of control flow transfer to either the ‘normal’ label or the ‘exception’ label.
# If the callee function returns with the “ret” instruction, control flow will return to the “normal” label.
# If the callee (or any indirect callees) returns via the “resume” instruction or other exception handling mechanism,
# control is interrupted and continued at the dynamically nearest “exception” label.
#
# The ‘exception’ label is a landing pad for the exception.
# As such, ‘exception’ label is required to have the “landingpad” instruction,
# which contains the information about the behavior of the program after unwinding happens,
# as its first non-PHI instruction. The restrictions on the “landingpad” instruction’s tightly couples it to the
# “invoke” instruction, so that the important information contained within the “landingpad” instruction can’t be
# lost through normal code motion.
#
# <result> = invoke [cconv] [ret attrs] [addrspace(<num>)] <ty>|<fnty> <fnptrval>(<function args>) [fn attrs]
#              [operand bundles] to label <normal label> unwind label <exception label>


def analyze_invoke(tokens):
    invoke = Invoke()

    # pop potential assignment
    while tokens[0] != "invoke":
        tokens.pop(0)

    tokens.pop(0)

    # pop calling convention
    if is_calling_convention(tokens[0]):
        attr = tokens.pop(0)
        if attr == "cc":
            attr += " {}".format(tokens.pop(0))
        invoke.set_calling_conv(attr)
    else:
        invoke.set_calling_conv("ccc")

    # check if there are parameter attributes
    while is_parameter_attribute(tokens[0]):
        open_brackets = tokens[0].count("(") - tokens[0].count(")")
        attr = tokens.pop(0)
        while open_brackets != 0:
            open_brackets += tokens[0].count("(") - tokens[0].count(")")
            attr += " {}".format(tokens.pop(0))
        invoke.add_ret_attr(attr)

    # pop optional address space field
    if is_address_space(tokens[0]):
        tokens.pop(0)

    # pop return type
    _, tokens = get_type(tokens)

    # get the function name
    if "bitcast" in tokens[0]:
        conversion = analyze_conversion(tokens)
        invoke.set_func(conversion.get_value())
    else:
        temp = tokens[0].split("(", 1)
        tokens[0] = temp[1]

        invoke.set_func(temp[0])

    while tokens:
        if tokens[0] == ")":
            tokens.pop(0)
            break

        count = 0
        for token in tokens:
            count += token.count("(") - token.count(")")
        if count == 0:
            break

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

        invoke.add_argument(argument)

    # read function attributes
    if tokens and is_group_attribute(tokens[0]):
        invoke.add_fn_attr(tokens[0])
        tokens.pop(0)
    while tokens and is_function_attribute(tokens[0]):
        if "allocsize" in tokens[0]:
            attribute = tokens.pop(0)
            open_brackets = attribute.count("(") - attribute.count(")")
            while open_brackets != 0:
                open_brackets += tokens[0].count("(") - tokens[0].count(")")
                attribute += " {}".format(tokens.pop(0))
            invoke.add_fn_attr(attribute)
        else:
            invoke.add_fn_attr(tokens.pop(0))

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

        invoke.set_operand_bundle_set(operand_bundle_set)

        # pop the ] token
        tokens.pop(0)

    # skip to the normal label
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


class Invoke(LlvmStatement):
    def __init__(self):
        super().__init__()
        self.func = None
        self.normal = None
        self.exception = None
        self.arguments = list()
        self.fn_attrs = list()
        self.operand_bundle_set = None
        self.cconv = None
        self.ret_attrs = list()

    def set_func(self, func):
        self.func = func

    def get_function_name(self):
        return self.func

    def set_normal(self, normal):
        self.normal = normal

    def get_normal(self):
        return self.normal

    def set_exception(self, exception):
        self.exception = exception

    def get_exception(self):
        return self.exception

    def add_argument(self, argument):
        self.arguments.append(argument)

    def get_arguments(self):
        return self.arguments

    def add_fn_attr(self, fn_attr):
        self.fn_attrs.append(fn_attr)

    def get_fn_attrs(self):
        return self.fn_attrs

    def set_operand_bundle_set(self, op_set):
        self.operand_bundle_set = op_set

    def get_operand_bundle_set(self):
        return self.operand_bundle_set

    def set_calling_conv(self, cconv):
        self.cconv = cconv

    def get_calling_conv(self):
        return self.cconv

    def add_ret_attr(self, attr):
        self.ret_attrs.append(attr)

    def get_ret_attrs(self):
        return self.ret_attrs

    def get_used_variables(self):
        variable_values = list()
        for argument in self.arguments:
            variable_values.append(argument.get_register())
        return variable_values


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
