from llvmAnalyser.types import get_type
from llvmAnalyser.values import get_value
from llvmAnalyser.llvmStatement import LlvmStatement

'''
Overview:
The 'getelementptr' instruction is used to get the address of a subelement of an aggregate data structure. It performs
address calculation only and does not access memory. The instruction can also be used to calculate a vector of such 
addresses.
<result> = getelementptr <ty>, <ty>* <ptrval>{, [inrange] <ty> <idx>}*
<result> = getelementptr inbounds <ty>, <ty>* <ptrval>{, [inrange] <ty> <idx>}*
<result> = getelementptr <ty>, <ptr vector> <ptrval>, [inrange] <vector index type> <idx>
'''


def analyze_getelementptr(tokens: list):
    op = Getelementptr()

    # skip potential assignment tokens
    while tokens[0] != "getelementptr":
        tokens.pop(0)

    # pop getelementptr
    tokens.pop(0)

    # pop a potential inbounds keyword
    if tokens[0] == "inbounds":
        tokens.pop(0)

    # pop the type
    _, tokens = get_type(tokens)

    # pop the second type
    _, tokens = get_type(tokens)

    # get the value
    value, tokens = get_value(tokens)
    op.set_value(value)

    # access potential further indices
    while len(tokens) != 0:
        if tokens[0] == "inrange":
            tokens.pop(0)

        # get the index type
        _, tokens = get_type(tokens)

        # get the index value
        op.add_index(tokens.pop(0).replace(",", ""))

    return op


class Getelementptr(LlvmStatement):
    def __init__(self):
        super().__init__()
        self.value = None
        self.indices = list()

    def set_value(self, value):
        self.value = value

    def get_value(self):
        return self.value

    def add_index(self, index):
        self.indices.append(index)

    def get_indices(self):
        return self.indices

    def get_used_variables(self):
        return [self.value]
