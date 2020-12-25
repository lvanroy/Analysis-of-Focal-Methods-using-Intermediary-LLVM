from llvmAnalyser.types import get_type
from llvmAnalyser.values import get_value
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
    temp, tokens = get_type(tokens)
    store_value, tokens = get_value(tokens)
    store.set_value(store_value)
    # skip type
    _, tokens = get_type(tokens)

    # get the register
    register, tokens = get_value(tokens)
    store.set_register(register)

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
