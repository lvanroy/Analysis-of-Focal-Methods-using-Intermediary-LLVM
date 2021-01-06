from llvmAnalyser.types import get_type
from llvmAnalyser.values import get_value
from llvmAnalyser.llvmStatement import LlvmStatement
# The ‘resume’ instruction is a terminator instruction that has no successors.
#
# resume <type> <value>


def analyze_resume(tokens):
    resume = Resume()

    # pop the resume instruction
    tokens.pop(0)

    # get the ex type
    ex_type, tokens = get_type(tokens)
    resume.set_type(ex_type)

    # get the value
    value, tokens = get_value(tokens)
    resume.set_value(value)

    return resume


class Resume(LlvmStatement):
    def __init__(self):
        super().__init__()
        self.ex_type = None
        self.value = None

    def set_type(self, ex_type):
        self.ex_type = ex_type

    def get_type(self):
        return self.ex_type

    def set_value(self, value):
        self.value = value

    def get_value(self):
        return self.value

    def get_used_variables(self):
        return [self.value]
