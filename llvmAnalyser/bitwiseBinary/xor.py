from llvmAnalyser.types import get_type
from llvmAnalyser.llvmStatement import LlvmStatement

'''
Overview:
bitwise exclusive or
'''


class XorAnalyzer:
    def __init__(self):
        pass

    @staticmethod
    def analyze_xor(tokens):
        xor = Xor()

        # pop the potential assignment
        while tokens[0] != "xor":
            tokens.pop(0)

        # pop the xor instruction
        tokens.pop(0)

        # pop the type
        _, tokens = get_type(tokens)

        # get the first operand
        op1 = ""
        while "," not in tokens[0]:
            op1 += tokens.pop(0)
        op1 += tokens.pop(0).replace(",", "")
        xor.set_op1(op1)

        # get the second operand
        op2 = ""
        while tokens:
            op2 += tokens.pop(0)
        xor.set_op2(op2)

        return xor


class Xor(LlvmStatement):
    def __init__(self):
        super().__init__()
        self.op1 = None
        self.op2 = None

    def set_op1(self, op):
        self.op1 = op

    def get_op1(self):
        return self.op1

    def set_op2(self, op):
        self.op2 = op

    def get_op2(self):
        return self.op2

    def get_used_variables(self):
        return [self.op1, self.op2]
