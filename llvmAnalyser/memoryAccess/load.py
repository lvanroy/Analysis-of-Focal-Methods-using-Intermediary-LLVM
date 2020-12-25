from llvmAnalyser.types import get_type
from llvmAnalyser.values import get_value
from llvmAnalyser.llvmStatement import LlvmStatement
# The ‘load’ instruction is used to read from memory.
# <result> = load [volatile] <ty>, <ty>* <pointer>[, align <alignment>]
#                                                 [, !nontemporal !<nontemp_node>]
#                                                 [, !invariant.load !<empty_node>]
#                                                 [, !invariant.group !<empty_node>]
#                                                 [, !nonnull !<empty_node>]
#                                                 [, !dereferenceable !<deref_bytes_node>]
#                                                 [, !dereferenceable_or_null !<deref_bytes_node>]
#                                                 [, !align !<align_node>][, !noundef !<empty_node>]
# <result> = load atomic [volatile] <ty>, <ty>* <pointer> [syncscope("<target-scope>")] <ordering>,
#            align <alignment> [, !invariant.group !<empty_node>]
# !<nontemp_node> = !{ i32 1 }
# !<empty_node> = !{}
# !<deref_bytes_node> = !{ i64 <dereferenceable_bytes> }
# !<align_node> = !{ i64 <value_alignment> }


def analyze_load(tokens):
    load = Load()

    # pop the assignment instruction
    while tokens[0] != "load":
        tokens.pop(0)

    # pop the load instruction
    tokens.pop(0)

    # check for atomic
    if tokens[0] == "atomic":
        tokens.pop(0)

    # check for volatile
    if tokens[0] == "volatile":
        tokens.pop(0)

    # skip type
    _, tokens = get_type(tokens)

    # check for ,
    if tokens[0] == ",":
        tokens.pop(0)

    # skip type
    _, tokens = get_type(tokens)

    # get the value
    value, tokens = get_value(tokens)
    load.set_value(value)

    return load


class Load(LlvmStatement):
    def __init__(self):
        super().__init__()
        self.value = None

    def set_value(self, value):
        self.value = value

    def get_value(self):
        return self.value

    def get_used_variables(self):
        return [self.value]
