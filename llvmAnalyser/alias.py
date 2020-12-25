from llvmAnalyser.llvmChecker import *
from llvmAnalyser.llvmStatement import LlvmStatement
from llvmAnalyser.types import get_type
# Aliases, unlike function or variables, don’t create any new data.
# They are just a new symbol and metadata for an existing position.
#
# @<Name> = [Linkage] [PreemptionSpecifier] [Visibility] [DLLStorageClass] [ThreadLocal]
#           [(unnamed_addr|local_unnamed_addr)] alias <AliaseeTy>, <AliaseeTy>* @<Aliasee>


def analyze_alias(tokens):
    alias = Alias()

    alias.set_name(tokens.pop(0))

    # pop assignment
    tokens.pop(0)

    while is_linkage_type(tokens[0]):
        tokens.pop(0)

    while is_runtime_preemptable(tokens[0]):
        tokens.pop(0)

    while is_visibility_style(tokens[0]):
        tokens.pop(0)

    while is_dll_storage_class(tokens[0]):
        tokens.pop(0)

    while is_tls(tokens[0]):
        tokens.pop(0)

    while is_unnamed_addr(tokens[0]):
        tokens.pop(0)

    # pop the alias token
    tokens.pop(0)

    # skip the alias type
    _, tokens = get_type(tokens)

    # skip the alias type pointer
    _, tokens = get_type(tokens)

    # get the alliasee
    alias.set_aliasee(tokens.pop(0))

    return alias


class Alias(LlvmStatement):
    def __init__(self):
        super().__init__()
        self.name = None
        self.aliasee = None

    def set_name(self, name):
        self.name = name

    def get_name(self):
        return self.name

    def set_aliasee(self, aliasee):
        self.aliasee = aliasee

    def get_aliasee(self):
        return self.aliasee
