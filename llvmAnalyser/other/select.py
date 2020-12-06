from llvmAnalyser.llvmStatement import LlvmStatement
from llvmAnalyser.llvmChecker import is_fast_math_flag
from llvmAnalyser.types import get_type
from llvmAnalyser.values import get_value
# The ‘select’ instruction is used to choose one value based on a condition, without IR-level branching.

# <result> = select [fast-math flags] selty <cond>, <ty> <val1>, <ty> <val2>             ; yields ty

# selty is either i1 or {<N x i1>}


def analyze_select(tokens):
    statement = Select()

    # pop the potential assignment
    while tokens[0] != "select":
        tokens.pop(0)

    # pop the select token
    tokens.pop(0)

    # pop the potential fast-math flags
    while is_fast_math_flag(tokens[0]):
        tokens.pop(0)

    # get the condition
    _, tokens = get_type(tokens)
    condition, tokens = get_value(tokens)
    statement.set_condition(condition)

    # get the if true option
    _, tokens = get_type(tokens)
    val1, tokens = get_value(tokens)
    statement.set_val1(val1)

    # get the if false option
    _, tokens = get_type(tokens)
    val2, tokens = get_value(tokens)
    statement.set_val2(val2)

    return statement


class Select(LlvmStatement):
    def __init__(self):
        super().__init__()
        self.condition = None
        self.val1 = None
        self.val2 = None

    def set_condition(self, condition):
        self.condition = condition

    def get_condition(self):
        return self.condition

    def set_val1(self, val1):
        self.val1 = val1

    def get_val1(self):
        return self.val1

    def set_val2(self, val2):
        self.val2 = val2

    def get_val2(self):
        return self.val2

    def get_used_variables(self):
        return [self.condition, self.val1, self.val2]
