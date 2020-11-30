from llvmAnalyser.llvmStatement import LlvmStatement
from llvmAnalyser.types import get_type
from llvmAnalyser.values import get_value


# The ‘shufflevector’ instruction constructs a permutation of elements from two input vectors,
# returning a vector with the same element type as the input and length that is the same as the shuffle mask.

# <result> = shufflevector <n x <ty>> <v1>, <n x <ty>> <v2>, <m x i32> <mask>
# <result> = shufflevector <vscale x n x <ty>> <v1>, <vscale x n x <ty>> v2, <vscale x m x i32> <mask>

def analyze_shufflevector(tokens):
    statement = Shufflevector()

    # pop potential assignment
    while tokens[0] != "shufflevector":
        tokens.pop(0)

    # pop the shufflevector token
    tokens.pop(0)

    # get the first vector type
    _, tokens = get_type(tokens)

    # get the first vector value
    value, tokens = get_value(tokens)
    statement.set_first_vector_value(value)

    # get the second vector type
    _, tokens = get_type(tokens)

    # get the second vector value
    value, tokens = get_value(tokens)
    statement.set_second_vector_value(value)

    # get the third vector type
    _, tokens = get_type(tokens)

    # get the third vector value
    value, tokens = get_value(tokens)
    statement.set_third_vector_value(value)

    return statement


class Shufflevector(LlvmStatement):
    def __init__(self):
        super().__init__()
        self.first_vector_value = None
        self.second_vector_value = None
        self.third_vector_value = None

    def set_first_vector_value(self, value):
        self.first_vector_value = value

    def get_first_vector_value(self):
        return self.first_vector_value

    def set_second_vector_value(self, value):
        self.second_vector_value = value

    def get_second_vector_value(self):
        return self.second_vector_value

    def set_third_vector_value(self, value):
        self.third_vector_value = value

    def get_third_vector_value(self):
        return self.third_vector_value

    def get_used_variables(self):
        return [self.first_vector_value, self.second_vector_value, self.third_vector_value]
