from llvmAnalyser.types import get_type


class BinaryOpAnalyzer:
    def __init__(self):
        self.operations = ["add"]
        self.op_symbols = {
            "add": "+"
        }

    def analyze_binary_op(self, tokens: list):
        op = BinOp()

        # pop the assignment
        while tokens[0] not in self.operations:
            tokens.pop(0)

        # pop the operation
        op.set_op(self.op_symbols[tokens.pop(0)])

        # pop potential nsw token
        if tokens[0] == "nsw":
            tokens.pop(0)

        # pop potential nuw token
        if tokens[0] == "nuw":
            tokens.pop(0)

        # get the type
        _, tokens = get_type(tokens)

        # get the first op
        value1 = ""
        while "," not in tokens[0]:
            value1 += tokens.pop(0)
        value1 += tokens.pop(0).replace(",", "")
        op.set_value1(value1)

        # get the second op
        value2 = "".join(tokens)
        op.set_value2(value2)

        return op


class BinOp:
    def __init__(self):
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
