from llvmAnalyser.types import get_type
from llvmAnalyser.llvmStatement import LlvmStatement


class LoadAnalyzer:
    def __init__(self):
        pass

    @staticmethod
    def analyze_load(tokens):
        load = Load()

        # pop the assignment instruction
        while tokens[0] != "load":
            tokens.pop(0)

        # pop the load instruction
        tokens.pop(0)

        # check for atomic
        if tokens[0] == "atomic":
            tokens.pop(0)

        # check for volatile
        if tokens[0] == "volatile":
            tokens.pop(0)

        # skip type
        _, tokens = get_type(tokens)

        # check for ,
        if tokens[0] == ",":
            tokens.pop(0)

        # skip type
        _, tokens = get_type(tokens)

        load.set_value(tokens[0].replace(",", ""))

        return load


class Load(LlvmStatement):
    def __init__(self):
        super().__init__()
        self.value = None

    def set_value(self, value):
        self.value = value

    def get_value(self):
        return self.value

    def get_used_variables(self):
        return [self.value]
