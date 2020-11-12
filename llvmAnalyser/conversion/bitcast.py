from llvmAnalyser.types import get_type
from llvmAnalyser.llvmStatement import LlvmStatement


class BitcastAnalyzer:
    def __init__(self):
        pass

    @staticmethod
    def analyze_bitcast(tokens):
        bitcast = Bitcast()

        # skip the initial assignment part
        while tokens[0] != "bitcast":
            tokens.pop(0)

        # pop the bitcast token
        tokens.pop(0)

        # get the original type
        original_type, tokens = get_type(tokens)
        bitcast.set_original_type(original_type)

        # get the value
        bitcast.set_value(tokens.pop(0))

        # get the final type
        tokens.pop(0)
        final_type, tokens = get_type(tokens)
        bitcast.set_final_type(final_type)

        return bitcast


class Bitcast(LlvmStatement):
    def __init__(self):
        super().__init__()
        self.value = None
        self.original_type = None
        self.final_type = None

    def set_value(self, value):
        self.value = value

    def set_original_type(self, original):
        self.original_type = original

    def set_final_type(self, final):
        self.final_type = final

    def get_value(self):
        return self.value

    def get_original_type(self):
        return self.original_type

    def get_final_type(self):
        return self.final_type

    def get_used_variables(self):
        return [self.value]
