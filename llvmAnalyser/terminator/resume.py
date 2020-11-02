from llvmAnalyser.types import get_type


class ResumeAnalyzer:
    def __init__(self):
        pass

    @staticmethod
    def analyze_resume(tokens):
        resume = Resume()

        # pop the resume instruction
        tokens.pop(0)

        # get the ex type
        ex_type, tokens = get_type(tokens)
        resume.set_type(ex_type)

        # get the value
        value = tokens.pop(0)
        resume.set_value(value)

        return resume


class Resume:
    def __init__(self):
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
