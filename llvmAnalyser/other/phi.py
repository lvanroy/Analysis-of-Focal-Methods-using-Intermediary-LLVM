from llvmAnalyser.types import get_type
from llvmAnalyser.llvmChecker import is_fast_math_flag
from llvmAnalyser.llvmStatement import LlvmStatement

'''
Overview:
A phi instruction is used to select a value depending on the predecessor block. will assign a value to an entry,
based upon the block it was in before the current block
'''


def analyze_phi(tokens):
    phi = Phi()

    # pop the potential assignment section
    while tokens[0] != "phi":
        tokens.pop(0)

    # pop the phi instruction
    tokens.pop(0)

    # pop the potential fast math flags
    while is_fast_math_flag(tokens[0]):
        tokens.pop(0)

    # pop the return type
    _, tokens = get_type(tokens)

    while tokens:
        option = PhiOption()

        # pop the '[' token
        tokens.pop(0)

        # get the value
        value = ""
        while "," not in tokens[0]:
            value += tokens.pop(0)
        tokens.pop(0).replace(",", "")
        option.set_value(value)

        # get the label
        label = ""
        while "]" not in tokens[0]:
            label += tokens.pop(0)
        option.set_label(label)

        # pop the ']' token
        tokens.pop(0)

        phi.add_option(option)

    return phi


class Phi(LlvmStatement):
    def __init__(self):
        super().__init__()
        self.options = list()

    def add_option(self, option):
        self.options.append(option)

    def get_options(self):
        return self.options

    def get_used_variables(self):
        used_vars = list()
        for option in self.options:
            used_vars.append(option.value)
        return used_vars


class PhiOption:
    def __init__(self):
        self.value = None
        self.label = None

    def set_value(self, value):
        self.value = value

    def get_value(self):
        return self.value

    def set_label(self, label):
        self.label = label

    def get_label(self):
        return self.label
