from llvmAnalyser.llvmStatement import LlvmStatement
from llvmAnalyser.types import get_type
from llvmAnalyser.values import get_value
# The ‘freeze’ instruction is used to stop propagation of undef and poison values.

# <result> = freeze ty <val>    ; yields ty:result


def analyze_freeze(tokens):
    statement = Freeze()

    # pop the potential assignment
    while tokens[0] != "freeze":
        tokens.pop(0)

    # pop the freeze token
    tokens.pop(0)

    # get the value
    _, tokens = get_type(tokens)
    value, tokens = get_value(tokens)
    statement.set_value(value)

    return statement


class Freeze(LlvmStatement):
    def __init__(self):
        super().__init__()
        self.value = None

    def set_value(self, value):
        self.value = value

    def get_value(self):
        return self.value

    def get_used_variables(self):
        return [self.value]
