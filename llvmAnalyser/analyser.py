from graph.node import Node
from llvmAnalyser.function import FunctionHandler
from llvmAnalyser.gtest import Gtest
from yaml import load

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader


# test_identifier must be a class that contains a identify test function member
# this function should return a boolean indicating whether or not the function is a test function

class LLVMAnalyser:
    def __init__(self):
        self.config = load(open('config.yml').read(), Loader=Loader)

        self.test_identifier = None
        if self.config["c++"]["test_framework"] == "gtest":
            self.test_identifier = Gtest

        self.function_handler = FunctionHandler()

    def analyse(self, file):
        f = open(file, "r")
        lines = f.readlines()
        f.close()

        for line in lines:
            tokens = line.split(" ")
            self.function_handler.identify_function(tokens)

        if self.config["debug"]:
            print(self.function_handler)
