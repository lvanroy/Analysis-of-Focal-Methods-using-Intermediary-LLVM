import re

from llvmAnalyser.testingFramework.testingFramework import TestingFramework


class Gtest(TestingFramework):
    def __init__(self):
        super().__init__()

    @staticmethod
    def identify_test_function(line):
        if "TestBodyEv" in line:
            return True
        else:
            return False

    @staticmethod
    def identify_assertion_function(line):
        # this identifies the function as being an internal gtest assertion function
        # the code that follows the specified prefix specifies the assertion type
        #   eg @_ZN7testing8internal11CmpHelperEQ will evaluate equality
        func = re.compile(r'^@_ZN7testing8internal.*CmpHelper(?!.*Failure.*)')
        if func.match(line):
            return True

        return False
