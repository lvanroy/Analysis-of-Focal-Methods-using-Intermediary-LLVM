from llvmAnalyser.types import get_type
from llvmAnalyser.values import get_value

from llvmAnalyser.llvmStatement import LlvmStatement
# The ‘extractvalue’ instruction extracts the value of a member field from an aggregate value.
# <result> = extractvalue <aggregate type> <val>, <idx>{, <idx>}*


def analyze_extractvalue(tokens):
    extractvalue = Extractvalue()

    # skip initial assignment part
    while tokens[0] != "extractvalue":
        tokens.pop(0)

    # pop the extractvalue token
    tokens.pop(0)

    # pop the type
    _, tokens = get_type(tokens)

    # get the value
    value, tokens = get_type(tokens)
    extractvalue.set_value(value)

    # get the indices
    while len(tokens) != 0:
        index, tokens = get_value(tokens)
        extractvalue.add_index(index)

    return extractvalue


class Extractvalue(LlvmStatement):
    def __init__(self):
        super().__init__()
        self.value = None
        self.indices = list()

    def set_value(self, value):
        self.value = value

    def add_index(self, index):
        self.indices.append(index)

    def get_value(self):
        return self.value

    def get_indices(self):
        return self.indices

    def get_used_variables(self):
        return [self.value]
