from llvmAnalyser.llvmStatement import LlvmStatement
from llvmAnalyser.types import get_type
from llvmAnalyser.values import get_value
# The instructions in this category are the conversion instructions (casting)
# which all take a single operand and a type. They perform various bit conversions on the operand.

# trunc .. to: <result> = trunc <ty> <value> to <ty2>
# zext .. to: <result> = zext <ty> <value> to <ty2>
# sext .. to: <result> = sext <ty> <value> to <ty2>
# fptrunc .. to: <result> = fptrunc <ty> <value> to <ty2>
# fpext .. to: <result> = fpext <ty> <value> to <ty2>
# fptoui .. to: <result> = fptoui <ty> <value> to <ty2>
# fptosi .. to: <result> = fptosi <ty> <value> to <ty2>
# uitofp .. to: <result> = uitofp <ty> <value> to <ty2>
# sitofp .. to: <result> = sitofp <ty> <value> to <ty2>
# ptrtoint .. to: <result> = ptrtoint <ty> <value> to <ty2>
# inttoptr .. to: <result> = inttoptr <ty> <value> to <ty2>[, !dereferenceable !<deref_bytes_node>]
#                                                          [, !dereferenceable_or_null !<deref_bytes_node>]
# bitcast .. to: <result> = bitcast <ty> <value> to <ty2>
# addrspacecast .. to:  <result> = addrspacecast <pty> <ptrval> to <pty2>


def analyze_conversion(tokens):
    statement = Conversion()

    # pop the assignment
    if tokens[1] == "=":
        tokens.pop(0)
        tokens.pop(0)

    # pop the operation
    statement.set_operation(tokens.pop(0))

    # check if the first token starts with an opening bracket
    # this happens when this object is an argument in a different statement, in those cases, to prevent
    # confusion with commas, certain sub statements can get enclosed within brackets
    final_index = len(tokens)
    if tokens[0][0] == "(":
        tokens[0] = tokens[0][1:]

        open_brackets = 1

        # loop over the tokens until this first bracket is closed again, when this happens, return the index
        for i in range(len(tokens)):
            for j in range(len(tokens[i])):
                char = tokens[i][j]
                if char == "(":
                    open_brackets += 1
                elif char == ")":
                    open_brackets -= 1
                if open_brackets == 0:
                    if tokens[i][j+1:] != "":
                        tokens.insert(i+1, tokens[i][j+1:])
                    tokens[i] = tokens[i][:j]
                    final_index = i
                    break
            if final_index != len(tokens):
                break

    start_len = len(tokens)

    # get the original value
    temp, tokens = get_type(tokens)
    value, tokens = get_value(tokens)
    statement.set_value(value)

    # pop the to token
    tokens.pop(0)

    final_index -= start_len - len(tokens)

    # get the final type
    final_type = ""
    while final_index > 0 and "dereferenceable" not in tokens[0]:
        final_type += tokens.pop(0)
        final_index -= 1

    statement.set_final_type(final_type)

    # pop potential remaining tokens
    while final_index > 0 and tokens and "dereferenceable" in tokens[0]:
        tokens.pop(0)
        tokens.pop(0)
        final_index -= 2

    return statement


class Conversion(LlvmStatement):
    def __init__(self):
        super().__init__()
        self.operation = None
        self.value = None
        self.final_type = None

    def set_operation(self, operation):
        self.operation = operation

    def get_operation(self):
        return self.operation

    def set_value(self, value):
        self.value = value

    def get_value(self):
        return self.value

    def set_final_type(self, final_type):
        self.final_type = final_type

    def get_final_type(self):
        return self.final_type

    def get_used_variables(self):
        return [self.value]
