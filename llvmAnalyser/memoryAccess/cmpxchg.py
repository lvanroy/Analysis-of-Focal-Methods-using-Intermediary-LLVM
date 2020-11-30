from llvmAnalyser.llvmStatement import LlvmStatement
from llvmAnalyser.types import get_type
from llvmAnalyser.values import get_value


# The ‘cmpxchg’ instruction is used to atomically modify memory.
# It loads a value in memory and compares it to a given value. If they are equal,
# it tries to store a new value into the memory.

# cmpxchg [weak] [volatile] <ty>* <pointer>, <ty> <cmp>, <ty> <new> [syncscope("<target-scope>")]
#                           <success ordering> <failure ordering>

def analyze_cmpxchg(tokens):
    statement = Cmpxchg()

    # pop a potential assignment instruction
    while tokens[0] != "cmpxchg":
        tokens.pop(0)

    # pop the cmpxchg token
    tokens.pop(0)

    # pop the weak token, if present
    if tokens[0] == "weak":
        tokens.pop(0)

    # pop the volatile token, if present
    if tokens[0] == "volatile":
        tokens.pop(0)

    # get the address value
    _, tokens = get_type(tokens)
    address, tokens = get_value(tokens)
    statement.set_address(address)

    # get the cmp value
    _, tokens = get_type(tokens)
    cmp, tokens = get_value(tokens)
    statement.set_cmp(cmp)

    # get the new value
    _, tokens = get_type(tokens)
    new, tokens = get_value(tokens)
    statement.set_new(new)

    # we are not interested in ordering instructions, and these can therefore be popped
    while tokens:
        tokens.pop(0)

    return statement


class Cmpxchg(LlvmStatement):
    def __init__(self):
        super().__init__()
        self.address = None
        self.cmp = None
        self.new = None

    def set_address(self, address):
        self.address = address

    def get_address(self):
        return self.address

    def set_cmp(self, cmp):
        self.cmp = cmp

    def get_cmp(self):
        return self.cmp

    def set_new(self, new):
        self.new = new

    def get_new(self):
        return self.new

    def get_used_variables(self):
        return [self.address, self.cmp, self.new]
