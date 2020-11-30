from llvmAnalyser.types import get_type
from llvmAnalyser.llvmStatement import LlvmStatement


def analyze_store(tokens):
    store = Store()

    # pop the store instruction
    tokens.pop(0)

    # check for atomic
    if tokens[0] == "atomic":
        tokens.pop(0)

    # check for volatile
    if tokens[0] == "volatile":
        tokens.pop(0)

    # skip type
    _, tokens = get_type(tokens)

    store.set_value(Value(tokens[0].replace(",", "")))
    tokens.pop(0)

    # skip type
    _, tokens = get_type(tokens)

    store.set_register(tokens[0].replace(",", ""))

    return store


class Store(LlvmStatement):
    def __init__(self):
        super().__init__()
        self.value = None
        self.register = None

    def set_value(self, value):
        self.value = value

    def set_register(self, register):
        self.register = register

    def get_value(self):
        return self.value

    def get_register(self):
        return self.register

    def get_used_variables(self):
        return [self.value]


class Value(LlvmStatement):
    def __init__(self, value):
        super().__init__()
        self.value = value

        if "%" in value:
            self.used_vars = [value]
        else:
            self.used_vars = None

    def get_value(self):
        return self.value

    def get_used_variables(self):
        return self.used_vars

    def __str__(self):
        return self.value
