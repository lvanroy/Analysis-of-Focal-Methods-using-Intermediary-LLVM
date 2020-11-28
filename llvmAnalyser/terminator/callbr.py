from llvmAnalyser.llvmStatement import LlvmStatement
from llvmAnalyser.types import get_type
# analyzer for the callbr command that will be of the form given below
# the address argument given is the address of the label to jump to
# <result> = callbr [cconv] [ret attrs] [addrspace(<num>)] <ty>|<fnty> <fnptrval>(<function args>) [fn attrs]
#                   [operand bundles] to label <fallthrough label> [indirect labels]


class CallBrAnalyzer:
    def __init__(self):
        pass

    @staticmethod
    def analyze_callbr(tokens: list):
        br = CallBr()

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


class CallBr(LlvmStatement):
    def __init__(self):
        super().__init__()
