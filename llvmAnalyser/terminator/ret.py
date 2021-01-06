from llvmAnalyser.llvmStatement import LlvmStatement
from llvmAnalyser.types import get_type
from llvmAnalyser.values import get_value
# The ‘ret’ instruction is used to return control flow (and optionally a value) from a function back to the caller.
#
# There are two forms of the ‘ret’ instruction:
#   one that returns a value and then causes control flow,
#   and one that just causes control flow to occur.
#
# ret <type> <value>       ; Return a value from a non-void function
# ret void                 ; Return from void function


def analyze_ret(tokens: list):
    ret = Ret()

    # pop the return command
    tokens.pop(0)

    # get the return type
    ret_type, tokens = get_type(tokens)

    # if any, get the return value
    if ret_type != "void":
        ret_value, tokens = get_value(tokens)
        ret.set_value(ret_value)

    return ret


class Ret(LlvmStatement):
    def __init__(self):
        super().__init__()
        self.value = None

    def set_value(self, value):
        self.value = value

    def get_value(self):
        return self.value
