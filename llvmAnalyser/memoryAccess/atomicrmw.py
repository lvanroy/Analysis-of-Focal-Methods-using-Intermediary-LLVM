from llvmAnalyser.llvmStatement import LlvmStatement
from llvmAnalyser.types import get_type
from llvmAnalyser.values import get_value
# The ‘atomicrmw’ instruction is used to atomically modify memory.

# atomicrmw [volatile] <operation> <ty>* <pointer>, <ty> <value> [syncscope("<target-scope>")] <ordering>


def analyze_atomicrmw(tokens):
    statement = Atomicrmw()

    # pop potential assignment
    while tokens[0] != "atomicrmw":
        tokens.pop(0)

    # pop the atomicrmw token
    tokens.pop(0)

    # pop the potential volatile token
    if tokens[0] == "volatile":
        tokens.pop(0)

    # pop the operation
    operation = tokens.pop(0)
    statement.set_operation(operation)

    # pop the address
    _, tokens = get_type(tokens)
    address, tokens = get_value(tokens)
    statement.set_address(address)

    # pop the value
    _, tokens = get_type(tokens)
    value, tokens = get_value(tokens)
    statement.set_value(value)

    # we are not interested in ordering, we can therefore pop all remaining tokens
    while tokens:
        tokens.pop(0)

    return statement


class Atomicrmw(LlvmStatement):
    def __init__(self):
        super().__init__()
        self.operation = None
        self.address = None
        self.value = None

    def set_operation(self, operation):
        self.operation = operation

    def get_operation(self):
        return self.operation

    def set_address(self, address):
        self.address = address

    def get_address(self):
        return self.address

    def set_value(self, value):
        self.value = value

    def get_value(self):
        return self.value

    def get_used_variables(self):
        return [self.address, self.value]
