import re

from graph.node import Node
from llvmAnalyser.llvmStatement import LlvmStatement
from llvmAnalyser.memoryAccess.getelementptr import Getelementptr
from llvmAnalyser.memoryAccess.store import Store
from llvmAnalyser.other.call import Call
from llvmAnalyser.terminator.callbr import CallBr
from llvmAnalyser.terminator.invoke import Invoke


# this function will return the mutation type
# the supported types are:
#   mutator: the function modifies the tracked variable
#   inspector: the function inspects and does not modify anything
#   uncertain: the function might modify the tracked variable
#


# def is_ret_mutated(tracked_variable, memory, depth=0):
#     if not memory.is_reg_in_mem(tracked_variable.value):
#         return "inspector"
#
#     rvalue = memory.get_val(tracked_variable.value)
#
#     if isinstance(rvalue, BinOp):
#         return True
#
#     elif isinstance(rvalue, str) and rvalue[0] == "%":
#         return is_ret_mutated(rvalue, memory)
#
#     # else:
#     #     print("uncaught statement: {}".format(rvalue))
#
#     mutator = False
#     for variable in rvalue.get_used_variables():
#         mutator = mutator or is_ret_mutated(variable, memory)
#         if mutator:
#             break
#
#     if mutator:
#         return "mutator"
#     else:
#         return "inspector"


def is_arg_mutated(current_node: Node, tracked_variable: Value):
    # if it does not satisfy the regex, it means it is a constant
    if not re.match(r'^%\d*?$', tracked_variable.value):
        return "inspector"

    inspector = "inspector"

    node_name = current_node.get_name()
    context = current_node.get_context()
    if re.match(r'%\d*? = .*?', node_name):
        variable, expression = node_name.split(" = ")

        if isinstance(context, Getelementptr):
            new_val = Value(context.get_value(), True)
            for inc in current_node.get_incs():
                new_inspector = is_arg_mutated(inc, new_val)
                if new_inspector == "mutator":
                    return "mutator"
                elif new_inspector == "uncertain":
                    inspector = new_inspector

        elif isinstance(context, Store):
            if tracked_variable.is_reference():
                return "mutator"

        elif isinstance(context, (Call, CallBr, Invoke)):
            success = False
            for arg in context.get_arguments():
                if arg.get_register() == tracked_variable.value:
                    success = True

            if success:
                is_arg_mutated()


    lvalues = memory.get_lvals(register)

    if not lvalues:
        return "inspector"

    mut_type = "inspector"

    for lvalue in lvalues:

        rvalue_addr = memory.get_val(lvalue)

        if rvalue_addr is not None:
            mut_type = is_arg_mutated(lvalue, memory, tracked_variable, depth)
            if mut_type == "mutator":
                return "mutator"
            elif mut_type == "uncertain":
                mut_type = "uncertain"

        rvalue_mem = memory.get_addr_val(lvalue)

        # a potential assignment to memory occurred
        if rvalue_mem is not None:
            if rvalue_addr is not None:
                return "mutator"

            mut_type = is_arg_mutated(lvalue, memory, tracked_variable, depth)
            if mut_type == "mutator":
                return "mutator"
            elif mut_type == "uncertain":
                mut_type = "uncertain"

    return mut_type
