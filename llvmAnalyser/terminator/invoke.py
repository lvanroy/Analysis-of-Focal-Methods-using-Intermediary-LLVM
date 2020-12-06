from llvmAnalyser.llvmChecker import *
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
