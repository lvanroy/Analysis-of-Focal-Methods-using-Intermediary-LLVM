from llvmAnalyser.types import get_type
from llvmAnalyser.values import get_value
from llvmAnalyser.llvmStatement import LlvmStatement


# Overview:
# shl:  <result> = shl [nuw] [nsw] <ty> <op1>, <op2>
# lshr: <result> = lshr [exact] <ty> <op1>, <op2>
# ashr: <result> = ashr [exact] <ty> <op1>, <op2>
# and:  <result> = and <ty> <op1>, <op2>
# or:   <result> = or <ty> <op1>, <op2>
# xor:  <result> = xor <ty> <op1>, <op2>


class BitwiseBinaryAnalyzer:
    def __init__(self):
        pass

    @staticmethod
    def analyze_bitwise_binary(tokens):
        statement = BitwiseBinaryStatement()

        # pop the potential assignment
        while tokens[0] not in ["shl", "lshr", "ashr", "and", "or", "xor"]:
            tokens.pop(0)

        # pop the bin instruction
        statement.set_statement_type(tokens.pop(0))

        # pop potential nuw token
        if tokens[0] == "nuw":
            tokens.pop(0)

        # pop potential nsw token
        if tokens[0] == "nsw":
            tokens.pop(0)

        # pop potential exact token
        if tokens[0] == "exact":
            tokens.pop(0)

        # pop the type
        _, tokens = get_type(tokens)

        # get the first operand
        op1, tokens = get_value(tokens)
        statement.set_op1(op1)

        # get the second operand
        op2, tokens = get_value(tokens)
        statement.set_op2(op2)

        return statement


class BitwiseBinaryStatement(LlvmStatement):
    def __init__(self):
        super().__init__()
        self.statement_type = None
        self.op1 = None
        self.op2 = None

    def set_statement_type(self, statement_type):
        self.statement_type = statement_type

    def get_statement_type(self):
        return self.statement_type

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
