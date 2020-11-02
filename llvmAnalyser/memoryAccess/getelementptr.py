from llvmAnalyser.types import get_type

'''
Overview:
The 'getelementptr' instruction is used to get the address of a subelement of an aggregate data structure. It performs
address calculation only and does not access memory. The instruction can also be used to calculate a vector of such 
addresses.
'''


class GetelementptrAnalyzer:
    def __init__(self):
        pass

    @staticmethod
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
        op.set_value(tokens.pop(0).replace(",", ""))

        # access potential further indices
        while len(tokens) != 0:
            if tokens[0] == "inrange":
                tokens.pop(0)

            # get the index type
            _, tokens = get_type(tokens)

            # get the index value
            op.add_index(tokens.pop(0))

        return op


class Getelementptr:
    def __init__(self):
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
