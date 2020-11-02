from llvmAnalyser.types import get_type


class ExtractvalueAnalyzer:
    def __init__(self):
        pass

    @staticmethod
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
        extractvalue.set_value(tokens.pop(0).replace(",", ""))

        # get the indices
        while len(tokens) != 0:
            extractvalue.add_index(tokens.pop(0).replace(",", ""))

        return extractvalue


class Extractvalue:
    def __init__(self):
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
