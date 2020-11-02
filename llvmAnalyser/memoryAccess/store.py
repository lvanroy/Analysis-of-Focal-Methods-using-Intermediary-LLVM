from llvmAnalyser.types import get_type


class StoreAnalyzer:
    def __init__(self):
        pass

    @staticmethod
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

        store.set_value(tokens[0].replace(",", ""))
        tokens.pop(0)

        # skip type
        _, tokens = get_type(tokens)

        store.set_register(tokens[0].replace(",", ""))

        return store


class Store:
    def __init__(self):
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
