from llvmAnalyser.llvmStatement import LlvmStatement
from llvmAnalyser.types import get_type
# analyzer for the indirectbr command that will be of the form given below
# the address argument given is the address of the label to jump to
# indirectbr <somety>* <address>, [ label <dest1>, label <dest2> ]


class IndirectBrAnalyzer:
    def __init__(self):
        pass

    @staticmethod
    def analyze_inidrectbr(tokens: list):
        br = IndirectBr()

        # pop the br command
        tokens.pop(0)

        _, tokens = get_type(tokens)

        # pop the address specifier
        br.set_address(tokens.pop(0).replace(",", ""))

        tokens.pop(0)
        # pop the labels
        while tokens[0] != "]":
            # pop the label token
            tokens.pop(0)

            # get the destination
            br.add_label(tokens.pop(0).replace(",", ""))

        return br


class IndirectBr(LlvmStatement):
    def __init__(self):
        super().__init__()
        self.address = None
        self.labels = list()

    def set_address(self, address):
        self.address = address

    def get_address(self):
        return self.address

    def add_label(self, dest):
        self.labels.append(dest)

    def get_labels(self):
        return self.labels
