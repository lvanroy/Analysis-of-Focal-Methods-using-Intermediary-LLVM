from llvmAnalyser.types import get_type
from llvmAnalyser.values import get_value
from llvmAnalyser.llvmStatement import LlvmStatement


# insertelement inserts a scalar element into a vector at a specfied index
# it follows the following syntax
# <result> = insertelement <n x <ty>> <val>, <ty> <elt>, <ty2> <idx>
# <result> = insertelement <vscale x n x <ty>> <val>, <ty> <elt>, <ty2> <idx>


def analyze_insertelement(tokens):
    statement = InsertElement()

    # pop the potential assignment
    while tokens[0] != "insertelement":
        tokens.pop(0)

    # pop the insertelement token
    tokens.pop(0)

    # get the vector type
    vector_type, tokens = get_type(tokens)
    statement.set_vector_type(vector_type)

    # pop the value token
    vector_value = get_value(tokens)
    statement.set_vector_value(vector_value)

    # skip the scalar element type
    _, tokens = get_type(tokens)

    # get the value element
    value, tokens = get_value(tokens)
    statement.set_scalar_value(value)

    # pop the type token
    _, tokens = get_type(tokens)

    # get the index
    statement.set_index(tokens.pop(0))

    return statement


class InsertElement(LlvmStatement):
    def __init__(self):
        super().__init__()
        self.vector_type = None
        self.vector_value = None
        self.scalar_value = None
        self.index = None

    def set_vector_type(self, vector_type):
        self.vector_type = vector_type

    def get_vector_type(self):
        return self.vector_type

    def set_vector_value(self, vector_value):
        self.vector_value = vector_value

    def get_vector_value(self):
        return self.vector_value

    def set_scalar_value(self, scalar_value):
        self.scalar_value = scalar_value

    def get_scalar_value(self):
        return self.scalar_value

    def set_index(self, index):
        self.index = index

    def get_index(self):
        return self.index

    def get_used_variables(self):
        return [self.vector_value]
