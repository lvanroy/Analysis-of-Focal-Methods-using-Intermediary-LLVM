from llvmAnalyser.types import get_type
from llvmAnalyser.values import get_value
from llvmAnalyser.llvmStatement import LlvmStatement
from llvmAnalyser.llvmChecker import is_fast_math_flag


class FpBinaryOpAnalyzer:
    def __init__(self):
        self.operations = ["fadd", "fsub", "fmul", "fdiv"]
        self.op_symbols = {
            "fadd": "+",
            "fsub": "-",
            "fmul": "*",
            "fdiv": "/"
        }

    def analyze_fp_binary_op(self, tokens: list):
        op = FpBinOp()

        # pop the assignment
        while tokens[0] not in self.operations:
            tokens.pop(0)

        # pop the operation
        op.set_op(self.op_symbols[tokens.pop(0)])

        # pop potential fastmath flags
        while is_fast_math_flag(tokens[0]):
            tokens.pop(0)

        # get the type
        _, tokens = get_type(tokens)

        # get the first op
        value1, tokens = get_value(tokens)
        op.set_value1(value1)

        # get the second op
        value2, tokens = get_value(tokens)
        op.set_value2(value2)

        return op


class FpBinOp(LlvmStatement):
    def __init__(self):
        super().__init__()
        self.operation = None
        self.value1 = None
        self.value2 = None

    def set_op(self, op):
        self.operation = op

    def get_op(self):
        return self.operation

    def set_value1(self, value1):
        self.value1 = value1

    def get_value1(self):
        return self.value1

    def set_value2(self, value2):
        self.value2 = value2

    def get_value2(self):
        return self.value2

    def get_used_variables(self):
        return [self.value1, self.value2]
