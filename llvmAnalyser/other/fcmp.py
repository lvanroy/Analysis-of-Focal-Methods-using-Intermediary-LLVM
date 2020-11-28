from llvmAnalyser.types import get_type
from llvmAnalyser.llvmStatement import LlvmStatement
from llvmAnalyser.llvmchecker import is_fast_math_flag


class FcmpAnalyzer:
    def __init__(self):
        pass

    @staticmethod
    def analyze_fcmp(tokens):
        fcmp = Fcmp()

        # pop the potential assignment instruction
        while tokens[0] != "fcmp":
            tokens.pop(0)

        # pop the fcmp instruction
        tokens.pop(0)

        # pop potential fast-math flags
        while is_fast_math_flag(tokens[0]):
            tokens.pop(0)

        # get the condition
        fcmp.set_condition(tokens.pop(0))

        # pop the type
        _, tokens = get_type(tokens)

        # get the first value
        value1 = ""
        while "," not in tokens[0]:
            value1 += tokens.pop(0)
        value1 += tokens.pop(0).replace(",", "")
        fcmp.set_value1(value1)

        value2 = ""
        while tokens:
            value2 += tokens.pop(0)
        fcmp.set_value2(value2)

        return fcmp


class Fcmp(LlvmStatement):
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
