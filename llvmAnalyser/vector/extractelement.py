from llvmAnalyser.types import get_type
from llvmAnalyser.values import get_value
from llvmAnalyser.llvmStatement import LlvmStatement


# extractelement extracts a single scalar element from a vector at a specfied index
# it follows the following syntax
# <result> = extractelement <n x <ty>> <val>, <ty2> <idx>
# <result> = extractelement <vscale x n x <ty>> <val>, <ty2> <idx>


def analyze_extractelement(tokens):
    statement = ExtractElement()

    # pop the potential assignment
    while tokens[0] != "extractelement":
        tokens.pop(0)

    # pop the extractelement token
    tokens.pop(0)

    # get the vector type
    vector_type, tokens = get_type(tokens)
    statement.set_vector_type(vector_type)

    # pop the value token
    vector_value, tokens = get_value(tokens)
    statement.set_vector_value(vector_value)

    # pop the type token
    _, tokens = get_type(tokens)

    # get the index
    index_value, tokens = get_value(tokens)
    statement.set_index(index_value)

    return statement


class ExtractElement(LlvmStatement):
    def __init__(self):
        super().__init__()
        self.vector_type = None
        self.vector_value = None
        self.index = None

    def set_vector_type(self, vector_type):
        self.vector_type = vector_type

    def get_vector_type(self):
        return self.vector_type

    def set_vector_value(self, vector_value):
        self.vector_value = vector_value

    def get_vector_value(self):
        return self.vector_value

    def set_index(self, index):
        self.index = index

    def get_index(self):
        return self.index

    def get_used_variables(self):
        return [self.vector_value]
