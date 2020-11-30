from llvmAnalyser.types import get_type
from llvmAnalyser.values import get_value
from llvmAnalyser.llvmStatement import LlvmStatement


def analyze_icmp(tokens):
    icmp = Icmp()

    # pop the potential assignment instruction
    while tokens[0] != "icmp":
        tokens.pop(0)

    # pop the icmp instruction
    tokens.pop(0)

    # get the condition
    icmp.set_condition(tokens.pop(0))

    # pop the type
    _, tokens = get_type(tokens)

    # get the first value
    value1, tokens = get_value(tokens)
    icmp.set_value1(value1)

    # get the second value
    value2, tokens = get_value(tokens)
    icmp.set_value2(value2)

    return icmp


class Icmp(LlvmStatement):
    def __init__(self):
        super().__init__()
        self.condition = None
        self.value1 = None
        self.value2 = None

    def set_condition(self, condition):
        self.condition = condition

    def get_condition(self):
        return self.condition

    def set_value1(self, value):
        self.value1 = value

    def get_value1(self):
        return self.value1

    def set_value2(self, value):
        self.value2 = value

    def get_value2(self):
        return self.value2

    def get_used_variables(self):
        return [self.value1, self.value2]
