from llvmAnalyser.types import get_type
from llvmAnalyser.llvmStatement import LlvmStatement
# The ‘switch’ instruction is used to transfer control flow to one of several different places.
# It is a generalization of the ‘br’ instruction, allowing a branch to occur to one of many possible destinations.
# switch <intty> <value>, label <defaultdest> [ <intty> <val>, label <dest> ... ]


def analyze_switch(tokens):
    switch = Switch()

    # pop the switch label
    tokens.pop(0)

    # pop the condition
    _, tokens = get_type(tokens)
    tokens.pop(0)

    # get the default label
    tokens.pop(0)
    switch.set_default(tokens[0])
    tokens.pop(0)

    tokens.pop(0)

    while tokens[0] != "]":
        branch = Branch()

        # pop the compared value
        _, tokens = get_type(tokens)
        branch.set_condition(tokens[0].replace(",", ""))
        tokens.pop(0)

        # get the corresponding label
        tokens.pop(0)
        branch.set_destination(tokens[0])
        tokens.pop(0)

        switch.add_branch(branch)

    return switch


class Switch(LlvmStatement):
    def __init__(self):
        super().__init__()
        self.default = None
        self.branches = list()

    def set_default(self, default):
        self.default = default

    def get_default(self):
        return self.default

    def add_branch(self, branch):
        self.branches.append(branch)

    def get_branches(self):
        return self.branches

    def get_used_variables(self):
        return list()

    def __str__(self):
        output = "switch def: {}\n".format(self.default)
        for branch in self.branches:
            output += "{}\n".format(branch)
        return output


class Branch:
    def __init__(self):
        self.conditional_value = None
        self.destination_block = None

    def set_condition(self, condition):
        self.conditional_value = condition

    def set_destination(self, destination):
        self.destination_block = destination

    def get_condition(self):
        return self.conditional_value

    def get_destination(self):
        return self.destination_block

    def __str__(self):
        return "\tif = {}, goto {}".format(self.conditional_value, self.destination_block)
