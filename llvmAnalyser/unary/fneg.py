from llvmAnalyser.llvmStatement import LlvmStatement
from llvmAnalyser.llvmChecker import is_fast_math_flag
from llvmAnalyser.values import get_value
from llvmAnalyser.types import get_type
# The ‘fneg’ instruction returns the negation of its operand.
# <result> = fneg [fast-math flags]* <ty> <op1>   ; yields ty:result


def analyze_fneg(tokens):
    fneg = Fneg()

    # pop potential assignment
    while tokens[0] != "fneg":
        tokens.pop(0)

    # pop the fneg command
    tokens.pop(0)

    # pop potential fast math flags
    while is_fast_math_flag(tokens[0]):
        tokens.pop(0)

    # skip the type
    _, tokens = get_type(tokens)

    # get the value
    value, tokens = get_value(tokens)
    fneg.set_value(value)

    return fneg


class Fneg(LlvmStatement):
    def __init__(self):
        super().__init__()
        self.value = None

    def set_value(self, value):
        self.value = value

    def get_value(self):
        return self.value
