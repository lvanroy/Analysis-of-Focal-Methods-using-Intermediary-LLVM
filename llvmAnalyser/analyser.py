from graph.graph import Graph
from yaml import load
from copy import copy
import re

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

from llvmAnalyser.function import FunctionHandler
from llvmAnalyser.attributes import AttributeGroupHandler
from llvmAnalyser.alias import analyze_alias

from llvmAnalyser.terminator.ret import analyze_ret
from llvmAnalyser.terminator.br import analyze_br
from llvmAnalyser.terminator.switch import analyze_switch
from llvmAnalyser.terminator.indirectbr import analyze_inidrectbr
from llvmAnalyser.terminator.invoke import analyze_invoke, Invoke
from llvmAnalyser.terminator.callbr import analyze_callbr, CallBr
from llvmAnalyser.terminator.resume import analyze_resume

from llvmAnalyser.binary.binaryOp import BinaryOpAnalyzer

from llvmAnalyser.unary.fneg import analyze_fneg

from llvmAnalyser.bitwiseBinary.bitwiseBinary import analyze_bitwise_binary

from llvmAnalyser.vector.extractelement import analyze_extractelement
from llvmAnalyser.vector.insertelement import analyze_insertelement
from llvmAnalyser.vector.shufflevector import analyze_shufflevector

from llvmAnalyser.aggregate.insertvalue import analyze_insertvalue
from llvmAnalyser.aggregate.extractvalue import analyze_extractvalue

from llvmAnalyser.memoryAccess.store import analyze_store
from llvmAnalyser.memoryAccess.load import analyze_load, Load
from llvmAnalyser.memoryAccess.cmpxchg import analyze_cmpxchg
from llvmAnalyser.memoryAccess.atomicrmw import analyze_atomicrmw
from llvmAnalyser.memoryAccess.getelementptr import analyze_getelementptr, Getelementptr

from llvmAnalyser.conversion.conversion import analyze_conversion, Conversion

from llvmAnalyser.other.cmp import analyze_cmp
from llvmAnalyser.other.phi import analyze_phi
from llvmAnalyser.other.select import analyze_select
from llvmAnalyser.other.freeze import analyze_freeze
from llvmAnalyser.other.call import analyze_call, Call

block_start_format = re.compile(r'[0-9]*:')


# test_identifier must be a class that contains a identify test function member
# this function should return a boolean indicating whether or not the function is a test function

class LLVMAnalyser:
    def __init__(self):
        # load the config
        with open('config.yml', 'r') as f:
            self.config = load(f.read(), Loader=Loader)

        # register a test analyzer to determine which function signature should be used to discover which functions
        # are tests
        self.test_identifier = re.compile(self.config["test_function_signature"])
        self.assertion_identifier = re.compile(self.config["assertion_function_signature"])

        # store the lines of the llvm file
        self.lines = None

        # make handlers for the specific llvm statements
        self.function_handler = FunctionHandler()
        self.attribute_group_handler = AttributeGroupHandler()

        self.binary_op_analyzer = BinaryOpAnalyzer()

        # keep track of the graph objects
        self.graphs = dict()
        self.top_graph = Graph()
        self.top_graph_nodes = dict()

        # keep track of the nodes that are added to the graphs, so that new nodes can be connected to the
        # previous ones in the chain, the node stack is a dict where the keys are the blocks,
        # and the values the stacks for each block
        self.node_stack = dict()

        # keep track of which function is opened, to further complete the graph related to this function
        self.opened_function = None

        self.stores = dict()
        self.loads = dict()
        self.references = dict()
        self.conversions = dict()

        # keep track of what register we are assigning to (if any),
        # this is an object of type llvmAnalyser.memory.Register
        self.assignee = None

        # keep track of the rhs value of the assignment
        # this can be of any statement object part of the llvm analyzers
        self.rhs = None

        # track the evaluated functions, as well as the functions in queue to evaluate
        self.evaluated_functions = list()
        self.functions_to_evaluate = list()

        self.indent = 0

        self.references = dict()

    def get_relevant_functions(self, file):
        f = open(file, "r")
        self.lines = [line.rstrip() for line in f.readlines()]
        f.close()

        indexes = [i for i in range(len(self.lines)) if " alias " in self.lines[i]]

        # analyze all aliases specified within the llvm file
        aliases = dict()
        for index in reversed(indexes):
            line = self.lines.pop(index)
            tokens = list(filter(None, line.replace("\t", "").replace("\n", "").split(";")[0].split(" ")))
            alias = analyze_alias(tokens)
            aliases[alias.get_name()] = alias.get_aliasee()

        # get the line indices for all definitions
        indexes = [i for i in range(len(self.lines)) if "define" == self.lines[i][:6]]

        # iterate over the definitions and analyze all test functions
        function_names = dict()
        for index in reversed(indexes):
            m = re.search(r'(@.*?\()+?', self.lines[index])
            function_name = m.group()[:-1]
            function_names[function_name] = index

            if self.test_identifier.match(function_name):
                self.evaluated_functions.append(function_name)
                self.analyse(index)

        # track the depth, this depth implies the number of functions we traversed, starting from the test function
        # this is limited, as we do not want to evaluate every single function to maximize efficiency
        # per depth, analyze all function encountered within the previous depth
        depth = 1
        while depth <= self.config["max_depth"]:
            temp_copy = copy(self.functions_to_evaluate)
            self.evaluated_functions += self.functions_to_evaluate
            self.functions_to_evaluate.clear()
            for function_name in temp_copy:
                if not self.assertion_identifier.match(function_name):
                    if function_name in function_names:
                        self.analyse(function_names[function_name])
                    elif function_name in aliases:
                        self.analyse(function_names[aliases[function_name]])

            depth += 1

    def get_focal_methods(self):
        # keep track of the functions under test for each test function
        focal_methods = dict()

        for function in self.evaluated_functions:
            # skip all non test functions
            if not self.test_identifier.match(function):
                continue

            focal_methods[function] = set()

            # get the assertions used within the test function
            assertions = self.get_assertions(function)

            # look if the assertion has a corresponding focal method by calling the get_focal_method
            # function for each of the parameters of the assertion
            # not every assertion is guaranteed to lead to focal methods as some assertions might directly depend
            # on other assertions and not tested variables
            for assertion in assertions:
                for inc in assertion.get_incs():
                    for parameter in assertion.get_arguments():
                        # print("testing: {}".format(function))
                        # print("assertion: {}".format(assertion.get_name()))
                        # print("parameter: {}".format(parameter.get_name()))
                        methods = self.find_focal_methods(parameter.get_name(), inc)
                        focal_methods[function] = focal_methods[function].union(methods)

        # iterate over all defined graphs
        for graph in self.graphs:
            # we only want to draw test functions
            if self.graphs[graph].is_test_func():
                # draw the relevant graphs if desired
                if self.config["graph"]:
                    self.graphs[graph].export_graph(graph)

        # draw the top graph if desired
        if self.config["graph"]:
            self.top_graph.export_graph("top_level_graph")

        return focal_methods

    def get_assertions(self, function):
        assertions = list()

        for call in self.function_handler.get_calls(function):
            if self.assertion_identifier.match(call.get_context().get_function_name()):
                assertions.append(call)

        for callbr in self.function_handler.get_callbrs(function):
            if self.assertion_identifier.match(callbr.get_context().get_function_name()):
                assertions.append(callbr)

        for invoke in self.function_handler.get_invokes(function):
            if self.assertion_identifier.match(invoke.get_context().get_function_name()):
                assertions.append(invoke)

        return assertions

    # get all focal methods used within upper node in the graph
    # checked_states:
    #   the checked states variable is needed to detect loops,
    #   for each node it will track all tracked variables that have been checked starting from each node
    def find_focal_methods(self, test_var, test_node, checked_states=None):
        focal_methods = set()

        if checked_states is None:
            checked_states = dict()

        # check if the current state is registered within the checked states dictionary
        if test_node not in checked_states:
            checked_states[test_node] = set()

        # detect a loop, if no loop, register that we are currently investigating the tracked variable
        if test_var in checked_states[test_node]:
            return focal_methods
        else:
            checked_states[test_node].add(test_var)

        # if not register, we are dealing with a constant, which can never lead to a function under test
        if not re.match(r'^%\d*?$', test_var):
            return focal_methods

        node_name = test_node.get_name()
        context = test_node.get_context()

        # print("{}: {}".format(test_var, node_name))

        if re.match(r'^%\d*? = .*?', node_name):
            variable, expression = node_name.split(" = ")
            if isinstance(context, (Call, Invoke, CallBr)):
                # if we ended up at another assertion function, we need to stop tracing,
                # as this would mean double work
                if self.assertion_identifier.match(context.get_function_name()):
                    return focal_methods

                # check if the tracked variable was used as an argument in the function call
                test_arg_found = False
                args = context.get_arguments()
                for arg in args:
                    if arg.get_register() == test_var:
                        test_arg_found = True
                        break

                # if either the test var is used, or the test var is assigned by the return value of the function
                # we consider the function as being a potential mutator, and we go deeper into the function scope
                if variable == test_var or test_arg_found:
                    new_methods, mutator = self.find_focal_methods_for_function(test_node, checked_states)
                    # focal_methods = focal_methods.union(new_methods)
                    if mutator == "mutator":
                        # print("added mutator: {}".format(context.get_function_name()))
                        focal_methods.add(context.get_function_name())
                        return focal_methods
                    else:
                        # print("added methods: {}".format(new_methods))
                        focal_methods = focal_methods.union(new_methods)

                # if the test var is not used as an argument, and we did not assign to the test var, the function
                # can have no effect on the test var, and we will not evaluate it
                else:
                    for inc in test_node.get_incs():
                        new_methods = self.find_focal_methods(test_var, inc, checked_states)
                        focal_methods = focal_methods.union(new_methods)
                        # print("added methods 2: {}".format(new_methods))

            # if no function was called, but we did assign to our variable
            # continue over the other incoming edges, but now with the used variables of the current statement
            elif test_var == variable:
                for inc in test_node.get_incs():
                    for var in context.get_used_variables():
                        new_methods = self.find_focal_methods(var, inc, checked_states)
                        focal_methods = focal_methods.union(new_methods)
                        # print("added methods 3: {}".format(new_methods))

            else:
                for inc in test_node.get_incs():
                    new_methods = self.find_focal_methods(test_var, inc, checked_states)
                    focal_methods = focal_methods.union(new_methods)
                    # print("added methods 4: {}".format(new_methods))

        # if we are not dealing with an assignment
        else:
            if isinstance(context, (Call, Invoke, CallBr)):
                # if we ended up at another assertion function, we need to stop tracing,
                # as this would mean double work
                if self.assertion_identifier.match(context.get_function_name()):
                    return focal_methods

                # check if the tracked variable was used as an argument in the function call
                test_arg_found = False
                args = context.get_arguments()
                for arg in args:
                    if arg.get_register() == test_var:
                        test_arg_found = True
                        break

                # if the test arg did get used, we go deeper into the function scope, as this is a potential mutator
                if test_arg_found:
                    new_methods, mutator = self.find_focal_methods_for_function(test_node, checked_states)
                    # focal_methods = focal_methods.union(new_methods)
                    if mutator == "mutator":
                        # print("added mutator: {}".format(context.get_function_name()))
                        focal_methods.add(context.get_function_name())
                        return focal_methods
                    else:
                        # print("added methods 5: {}".format(new_methods))
                        focal_methods = focal_methods.union(new_methods)

                # if the test var did not get used, we just carry on with the incoming edges
                else:
                    for inc in test_node.get_incs():
                        new_methods = self.find_focal_methods(test_var, inc, checked_states)
                        focal_methods = focal_methods.union(new_methods)
                        # print("added methods 6: {}".format(new_methods))

            # if we are not considering a call, we carry on with the incoming edges
            else:
                for inc in test_node.get_incs():
                        new_methods = self.find_focal_methods(test_var, inc, checked_states)
                        focal_methods = focal_methods.union(new_methods)
                        # print("added methods 7: {}".format(new_methods))

        return focal_methods

    def find_focal_methods_for_function(self, test_node, checked_states):
        focal_methods = set()

        mutator = "inspector"

        context = test_node.get_context()
        arguments = context.get_arguments()
        function_name = context.get_function_name()

        if function_name in self.node_stack:
            for i in range(len(arguments)):
                root_arg = self.function_handler.get_function_arguments(function_name)[i]
                # noalias implies that the value it directs to can not be considered
                # if this is the case, it means that this is just instantiated for the function
                # and it can therefore not be mutated
                if "noalias" in root_arg.get_parameter_attributes():
                    continue
                arg_val = root_arg.get_register()
                self.indent = 0
                self.opened_function = function_name
                # print("entering function: {} using: {}".format(self.opened_function, arg_val))
                mutator = self.is_arg_mutated(arg_val)
                # print("function {}\nwas found to be {} for arg {}".format(function_name, mutator, arg_val))
                if mutator == "mutator":
                    focal_methods.add(function_name)
                    return focal_methods, "mutator"
                elif mutator == "uncertain":
                    focal_methods.add(function_name)
                    mutator = "uncertain"

            for i in range(len(arguments)):
                arg = arguments[i]
                reg = arg.get_register()
                for inc in test_node.get_incs():
                    focal_methods = focal_methods.union(self.find_focal_methods(reg, inc, checked_states))

        return focal_methods, mutator

    # see if an argument of a function is mutated within that function scope
    def is_arg_mutated(self, tracked_variable, is_ref=False):
        # print("{}:{}".format(tracked_variable, is_ref))
        mutation_type = "inspector"

        # this means the function was never analysed, and was therefore not defined our below our max depth
        if self.opened_function not in self.node_stack:
            return "uncertain"

        used_functions = self.function_handler.get_used_functions(self.opened_function)

        for used_function in used_functions:
            context = used_function.get_context()
            if tracked_variable in context.get_argument_registers() and context.get_function_name() in self.node_stack:
                temp = self.opened_function
                self.opened_function = context.get_function_name()
                index = context.get_argument_registers().index(tracked_variable)
                new_function_args = self.function_handler.get_function(self.opened_function).get_argument_registers()
                new_var = new_function_args[index]
                # print("entering function: {} using: {} ({})".format(self.opened_function, new_var, is_ref))
                mut = self.is_arg_mutated(new_var, is_ref)
                # print("exited function: {}".format(self.opened_function))
                self.opened_function = temp

                if mut == "mutator":
                    return "mutator"
                elif mut == "uncertain":
                    mutation_type = "uncertain"

        # this means we assigned to a reference to the tracked variable
        # the assigned value must also not be a reference, because otherwise we are considering a loop
        # considering the case below, %3 will be marked as if containing a reference, but then we assigned to a
        # reference, and so it might be considered a mutation, which is incorrect
        #   %1 = getelementptr %2
        #   store %1, %3
        stores = self.stores[self.opened_function]
        is_loaded = tracked_variable in self.loads[self.opened_function]
        is_stored = tracked_variable in stores
        is_referenced = tracked_variable in self.references[self.opened_function]
        if is_ref and ((is_stored and is_loaded) or (is_stored and is_referenced)):
            return "mutator"

        else:
            for lhs, rhs in self.stores[self.opened_function].items():
                # this means that we assigned our tracked variable to a dif variable
                if rhs == tracked_variable:
                    mut = self.is_arg_mutated(lhs, is_ref)

                    if mut == "mutator":
                        return "mutator"
                    elif mut == "uncertain":
                        mutation_type = "uncertain"

            for lhs, rhs in self.loads[self.opened_function].items():
                # this means that we loaded our tracked variable into a dif variable
                if rhs == tracked_variable:
                    mut = self.is_arg_mutated(lhs, False)

                    if mut == "mutator":
                        return "mutator"
                    elif mut == "uncertain":
                        mutation_type = "uncertain"

            for lhs, rhs in self.conversions[self.opened_function].items():
                # this means that we converted our tracked variable to a dif type
                if rhs == tracked_variable:
                    mut = self.is_arg_mutated(lhs, False)

                    if mut == "mutator":
                        return "mutator"
                    elif mut == "uncertain":
                        mutation_type = "uncertain"

            for var, ref in self.references[self.opened_function].items():
                # this means that we assigned a reference of our tracked variable to a dif variable
                if ref == tracked_variable:
                    mut = self.is_arg_mutated(var, True)

                    if mut == "mutator":
                        return "mutator"
                    elif mut == "uncertain":
                        mutation_type = "uncertain"

        return mutation_type

    def analyse(self, i):
        while i < len(self.lines):
            tokens = list(filter(None, self.lines[i].replace("\t", "").replace("\n", "").split(";")[0].split(" ")))

            if len(tokens) == 0:
                i += 1
                continue

            # register assignment
            if "=" in tokens and self.opened_function is not None:
                self.analyze_assignment(tokens)

            # register new function definition
            if tokens[0] == "define":
                self.analyze_define(tokens)

            # register attribute group
            elif tokens[0] == "attributes":
                self.analyze_attribute_group(tokens)

            # skip global scope
            elif self.opened_function is None:
                i += 1
                continue

            # Terminator instructions
            # -----------------------
            # Terminator instructions are used to end every basic block. It is used to redirect the execution
            # to the next code block.
            # The terminator instructions are:
            #   'ret', 'br', 'switch', 'indirectbr', 'invoke', 'callbr', 'resume'
            #   'catchswitch', 'catchret', 'cleanupret', 'unreachable'

            # register ret statement
            elif tokens[0] == "ret":
                self.register_return(tokens)

            # register br statement
            elif "br" in tokens:
                self.register_br(tokens)

            # register switch statement
            elif "switch" in tokens:
                while "]" not in tokens:
                    tokens += list(filter(None, self.lines[i + 1].replace("\t", "").replace("\n", "").split(" ")))
                    i += 1
                self.register_switch(tokens)

            # register indirectbr statement
            elif "indirectbr" in tokens:
                self.register_indirectbr(tokens)

            # register invoke statement
            elif "invoke" in tokens:
                tokens += list(filter(None, self.lines[i + 1].replace("\t", "").replace("\n", "").split(" ")))
                i += 1
                self.register_invoke(tokens)

            # register callbr statement
            elif "callbr" in tokens:
                self.register_callbr(tokens)

            # register resume statement
            elif "resume" in tokens:
                self.register_resume(tokens)

            # skip catchswitch
            elif "catchswitch" in tokens:
                i += 1
                continue

            # skip catchret
            elif "catchret" in tokens:
                i += 1
                continue

            # skip cleanupret
            elif "cleanupret" in tokens:
                i += 1
                continue

            # register unreachable statement
            elif "unreachable" in tokens:
                self.register_unreachable()

            # Unary operations
            # ----------------
            # Unary Operations
            # Unary operators require a single operand, execute an operation on it, and produce a single value.
            # The operand might represent multiple data, as is the case with the vector data type.
            # The result value has the same type as its operand.

            # register unary operation
            elif len(tokens) > 2 and tokens[2] == "fneg":
                self.register_fneg(tokens)

            # Binary operations
            # -----------------
            # Binary operations are used for most computations in a program. They require two operands of the same type
            # and it results in a single value on which the operation is applied.

            # register binary integer operation
            elif len(tokens) > 2 and tokens[2] in ["add", "sub", "mul", "sdiv", "srem", "udiv",
                                                   "urem", "fadd", "fsub", "fmul", "fdiv"]:
                self.register_binary_op(tokens)

            # Bitwise binary operations
            # -------------------------
            # Bitwise binary operations are used to do various forms of bit-twiddling in a program. They require two
            # operands of the same type, execute an operation on them, and produce a single value. The following
            # bitwise binary operations exist within llvm:
            #   'shl', 'lshr', 'ashr', 'and', 'or', 'xor'

            # register bitwise binary instruction
            elif len(tokens) > 2 and tokens[2] in ["shl", "lshr", "ashr", "and", "or", "xor"] and \
                    tokens[1] == "=":
                self.register_bitwise_binary(tokens)

            # Vector operations
            # -----------------
            # Vector operations cover element-access and vector-specific operations needed to process vectors
            # effectively.
            # The vector instructions are:
            #   'extractelement', 'insertelement', 'shufflevector'

            # register extractelement statement
            elif len(tokens) > 2 and tokens[2] == "extractelement":
                self.register_extractelement(tokens)

            # register insertelement statement
            elif len(tokens) > 2 and tokens[2] == "insertelement":
                self.register_insertelement(tokens)

            # register shufflevector statement
            elif len(tokens) > 2 and tokens[2] == "shufflevector":
                self.register_shufflevector(tokens)

            # Aggregate Operations
            # --------------------
            # Aggregate operations are instructions that allow us to work with aggregate values.
            # The aggregate instructions are:
            #   'extractvalue', 'insertvalue'

            # register extractvalue statement
            elif len(tokens) > 2 and tokens[2] == "extractvalue":
                self.register_extractvalue(tokens)

            # register insertvalue statement
            elif len(tokens) > 2 and tokens[2] == "insertvalue":
                self.register_insertvalue(tokens)

            # Memory Access and Addressing operations
            # ---------------------------------------
            # The following operations are used to read, write and allocate memory in LLVM:
            #   'alloca, 'load', 'store', 'fence', 'cmpxchg', 'atomicrmw', 'getelementptr'

            # register alloca statement
            elif "alloca" in tokens:
                self.assignee = None
                i += 1
                continue

            # register load statement
            elif "load" in tokens:
                self.register_load(tokens)

            # register store statement
            elif "store" in tokens:
                self.register_store(tokens)

            # register fence statement
            elif "fence" in tokens:
                i += 1
                continue

            # register cmpxchg statement
            elif "cmpxchg" in tokens:
                self.register_cmpxchg(tokens)

            # register atomicrmx statement
            elif "atomicrmw" in tokens:
                self.register_atomicrmw(tokens)

            # register getelementptr statement
            elif len(tokens) > 2 and tokens[2] == "getelementptr" and tokens[1] == "=":
                self.register_getelementptr(tokens)

            # Conversion operations
            # ---------------------
            # Conversion operations allow the casting of variables, the following conversion operations are defined
            # within LLVM:
            #   'trunc .. to', 'zext .. to', 'sext .. to', 'fptrunc .. to', 'fpext .. to',
            #   'fptoui .. to', 'fptosi .. to', 'uitofp .. to', 'sitofp .. to',
            #   'ptrtoint .. to', 'inttoptr .. to', 'bitcast .. to', 'addrspacecast .. to'

            # register conversion statement
            elif len(tokens) > 2 and tokens[2] in ["trunc", "zext", "sext", "fptrunc",
                                                   "fpext", "fptoui", "fptosi", "uitofp",
                                                   "sitofp", "ptrtoint", "inttoptr", "bitcast",
                                                   "addrspacecast"] \
                    and tokens[1] == "=":
                self.register_conversion(tokens)

            # other operations
            # ----------------
            # The other instructions are specified as other, due to lack of better classification. These are general
            # cross operation set operations. The llvm instruction set contains the following operations of type other:
            #   'icmp', 'fcmp', 'phi', 'select', 'freeze', 'call', 'va_arg', 'landingpad', 'catchpad', 'cleanuppad'

            # register icmp statement
            elif len(tokens) > 2 and tokens[1] == "=" and tokens[2] in ["icmp", "fcmp"]:
                self.register_cmp(tokens)

            # register phi statement
            elif len(tokens) > 2 and tokens[1] == "=" and tokens[2] == "phi":
                self.register_phi(tokens)

            # register select statement
            elif "select" in tokens:
                self.register_select(tokens)

            # register freeze statement
            elif "freeze" in tokens:
                self.register_freeze(tokens)

            # register function call
            elif "call" in tokens:
                self.analyze_call(tokens)

            # register landingpad statement
            elif "landingpad" in tokens:
                while True:
                    if "catch" in self.lines[i + 1]:
                        i += 1
                    elif "cleanup" in self.lines[i + 1]:
                        i += 1
                    elif "filter" in self.lines[i + 1]:
                        i += 1
                    else:
                        break

                self.assignee = None
                i += 1
                continue

            # register catchpad statement
            elif "catchpad" in tokens:
                self.assignee = None
                i += 1
                continue

            # register clenuppad statement
            elif "cleanuppad" in tokens:
                self.assignee = None
                i += 1
                continue

            # register new code block
            elif block_start_format.match(tokens[0]):
                opened_block = "{}:%{}".format(self.opened_function, tokens[0].split(":")[0])
                self.node_stack[self.opened_function].append(self.get_first_node_of_block(opened_block))

            # register end of function definition
            elif tokens[0] == "}":
                self.register_function_end()
                return

            elif self.opened_function is not None:
                print("Error: unregistered instruction!")
                print(tokens)
                print(self.lines[i])

            if self.assignee is not None:
                new_name = "{} = {}".format(self.assignee, self.node_stack[self.opened_function][-1].get_name())
                top_node = self.node_stack[self.opened_function][-1]
                top_node.set_name(new_name)

                if isinstance(self.rhs, Load):
                    self.loads[self.opened_function][self.assignee] = self.rhs.get_value()

                elif isinstance(self.rhs, Getelementptr):
                    self.references[self.opened_function][self.assignee] = self.rhs.get_value()

                elif isinstance(self.rhs, Conversion):
                    self.conversions[self.opened_function][self.assignee] = self.rhs.get_value()

                self.rhs = None
                self.assignee = None

            i += 1

        return

    def analyze_define(self, tokens):
        self.opened_function = self.function_handler.identify_function(tokens)
        self.stores[self.opened_function] = dict()
        self.loads[self.opened_function] = dict()
        self.references[self.opened_function] = dict()
        self.conversions[self.opened_function] = dict()
        self.graphs[self.opened_function] = Graph()
        self.node_stack[self.opened_function] = list()
        new_node = self.add_node(self.opened_function)
        if self.opened_function not in self.top_graph_nodes:
            top_graph_node = self.top_graph.add_node(self.opened_function)
            self.top_graph_nodes[self.opened_function] = top_graph_node
        if self.test_identifier.match(self.opened_function):
            self.top_graph_nodes[self.opened_function].set_test()
            self.graphs[self.opened_function].set_test_func()
            new_node.set_test()
            self.graphs[self.opened_function].add_assertion(new_node)
        if self.assertion_identifier.match(self.opened_function):
            self.top_graph_nodes[self.opened_function].set_assertion()
            new_node.set_assertion()

    def analyze_attribute_group(self, tokens):
        self.attribute_group_handler.identify_attribute_groups(tokens)

    # Analyze Terminator instructions
    # -------------------------------
    # register_return()
    # register_br()
    # register_switch()
    # register_indirectbr()
    # register_invoke()
    # register_callbr()
    # register_resume()
    # register_unreachable()

    def register_return(self, tokens):
        self.rhs = analyze_ret(tokens)
        if self.rhs.get_value() is not None:
            label = "ret {}".format(self.rhs.get_value())
        else:
            label = "ret"
        self.register_statement(label)

    def register_br(self, tokens):
        self.rhs = analyze_br(tokens)
        new_node = self.register_statement("br")

        block_name = "{}:{}".format(self.opened_function, self.rhs.get_label1())
        first_branch = self.get_first_node_of_block(block_name)
        self.graphs[self.opened_function].add_edge(new_node, first_branch)

        if self.rhs.get_label2() is not None:
            block_name = "{}:{}".format(self.opened_function, self.rhs.get_label2())
            second_branch = self.get_first_node_of_block(block_name)
            self.graphs[self.opened_function].add_edge(new_node, second_branch)

    def register_switch(self, tokens):
        self.rhs = analyze_switch(tokens)
        new_node = self.register_statement("switch")

        block_name = "{}:{}".format(self.opened_function, self.rhs.get_default())
        def_node = self.get_first_node_of_block(block_name)
        self.graphs[self.opened_function].add_edge(new_node, def_node, "default")

        for branch in self.rhs.get_branches():
            block_name = "{}:{}".format(self.opened_function, branch.get_destination())
            branch_node = self.get_first_node_of_block(block_name)
            self.graphs[self.opened_function].add_edge(new_node, branch_node, "= {}".format(branch.get_condition()))

    def register_indirectbr(self, tokens):
        self.rhs = analyze_inidrectbr(tokens)
        new_node = self.register_statement("indirectbr")

        for label in self.rhs.get_labels():
            block_name = "{}:{}".format(self.opened_function, label)
            branch_node = self.get_first_node_of_block(block_name)
            self.graphs[self.opened_function].add_edge(new_node, branch_node, "{} == {}".format(self.rhs.get_address(),
                                                                                                label))

    def register_invoke(self, tokens):
        self.rhs = analyze_invoke(tokens)
        func_name = self.rhs.get_function_name()
        new_node = self.register_statement("invoke {}".format(func_name))
        self.function_handler.add_invoke(self.opened_function, new_node)

        if func_name not in self.evaluated_functions and func_name not in self.functions_to_evaluate:
            self.functions_to_evaluate.append(func_name)

        for argument in self.rhs.get_arguments():
            argument_node = self.graphs[self.opened_function].add_node(argument.get_register())
            new_node.add_argument(argument_node)

        block_name = "{}:{}".format(self.opened_function, self.rhs.get_normal())
        normal_node = self.get_first_node_of_block(block_name)
        self.graphs[self.opened_function].add_edge(new_node, normal_node, "normal")

        block_name = "{}:{}".format(self.opened_function, self.rhs.get_exception())
        exception_node = self.get_first_node_of_block(block_name)
        self.graphs[self.opened_function].add_edge(new_node, exception_node, "exception")

        # move the main node to the back of the list, so that the assignment can be handled properly
        index = self.node_stack[self.opened_function].index(new_node)
        self.node_stack[self.opened_function].append(self.node_stack[self.opened_function].pop(index))

    def register_callbr(self, tokens):
        self.rhs = analyze_callbr(tokens)
        prev_node = self.node_stack[self.opened_function][-1]
        function_name = self.rhs.get_function_name()
        new_node = self.add_node("call {}".format(function_name), self.rhs)
        self.function_handler.add_callbr(self.opened_function, new_node)

        if function_name not in self.evaluated_functions and function_name not in self.functions_to_evaluate:
            self.functions_to_evaluate.append(function_name)

        for argument in self.rhs.get_function_arguments():
            argument_node = self.graphs[self.opened_function].add_node(argument.get_argument_name())
            new_node.add_argument(argument_node)

        self.graphs[self.opened_function].add_edge(prev_node, new_node)

        if function_name in self.top_graph_nodes:
            final_node = self.top_graph_nodes[function_name]
        else:
            final_node = self.top_graph.add_node(function_name)
            self.top_graph_nodes[function_name] = final_node
        first_node = self.top_graph_nodes[self.opened_function]
        self.top_graph.add_edge(first_node, final_node)

        # move the main node to the back of the list, so that the assignment can be handled properly
        index = self.node_stack[self.opened_function].index(new_node)
        self.node_stack[self.opened_function].append(self.node_stack[self.opened_function].pop(index))

    def register_resume(self, tokens):
        self.rhs = analyze_resume(tokens)
        node_name = "resume {} {}".format(self.rhs.get_type(), self.rhs.get_type())
        self.register_statement(node_name)

    def register_unreachable(self):
        prev_node = self.node_stack[self.opened_function][-1]

        new_node = self.add_node("unreachable")
        self.graphs[self.opened_function].add_edge(prev_node, new_node)

    # Analyze Unary operations
    # ------------------------
    # register_fneg()

    def register_fneg(self, tokens):
        self.rhs = analyze_fneg(tokens)
        node_name = "fneg {}".format(self.rhs.get_value())
        self.register_statement(node_name)

    # Analyze Binary operations
    # -------------------------
    # register_binary_op()

    def register_binary_op(self, tokens):
        self.rhs = self.binary_op_analyzer.analyze_binary_op(tokens)
        node_name = "{} {} {}".format(self.rhs.get_value1(), self.rhs.get_op(), self.rhs.get_value2())
        self.register_statement(node_name)

    # Analyze Bitwise Binary operations
    # ---------------------------------
    # register_bitwise_binary()

    def register_bitwise_binary(self, tokens):
        self.rhs = analyze_bitwise_binary(tokens)
        node_name = "{} {} {}".format(self.rhs.op1, self.rhs.get_statement_type(), self.rhs.op2)
        self.register_statement(node_name)

    # Analyze Vector operations
    # -------------------------
    # register_extractelement()
    # register_insertelement()
    # register_shufflevector()

    def register_extractelement(self, tokens):
        self.rhs = analyze_extractelement(tokens)
        node_name = "extract element from {} at index {}".format(self.rhs.get_vector_value(), self.rhs.get_index())
        self.register_statement(node_name)

    def register_insertelement(self, tokens):
        self.rhs = analyze_insertelement(tokens)
        node_name = "insert {} in {} at index {}".format(self.rhs.get_scalar_value(),
                                                         self.rhs.get_vector_type(),
                                                         self.rhs.get_index())
        self.register_statement(node_name)

    def register_shufflevector(self, tokens):
        self.rhs = analyze_shufflevector(tokens)
        node_name = "permute {} with {} using the pattern defined in {}".format(self.rhs.get_first_vector_value(),
                                                                                self.rhs.get_second_vector_value(),
                                                                                self.rhs.get_third_vector_value())
        self.register_statement(node_name)

    # Analyze Aggregate operations
    # ----------------------------
    # register_extractvalue()
    # register_insertvalue()

    def register_extractvalue(self, tokens):
        self.rhs = analyze_extractvalue(tokens)

        node_name = "extract value from {} at index ".format(self.rhs.get_value())
        for index in self.rhs.get_indices():
            node_name += "{}, ".format(index)

        self.register_statement(node_name[:-2])

    def register_insertvalue(self, tokens):
        self.rhs = analyze_insertvalue(tokens)

        if self.rhs.get_original() != "undef":
            node_name = "insert {} in {} at index ".format(self.rhs.get_insert_value(), self.rhs.get_original())
        else:
            node_name = "insert {} in new object of type {} at index ".format(self.rhs.get_insert_value(),
                                                                              self.rhs.get_object_type())
        for index in self.rhs.get_indices():
            node_name += "{}, ".format(index)

        self.register_statement(node_name[:-2])

    # Analyze Memory Access and Addressing operations
    # -----------------------------------------------
    # register_load()
    # register_store()
    # register_cmpxchg()
    # register_atomicrmw()
    # register_getelementptr()

    def register_load(self, tokens):
        self.rhs = analyze_load(tokens)
        self.register_statement(self.rhs.get_value())

    def register_store(self, tokens):
        self.rhs = analyze_store(tokens)
        self.register_statement("{} = {}".format(self.rhs.get_register(), str(self.rhs.get_value())))

        self.stores[self.opened_function][self.rhs.get_register()] = self.rhs.get_value()

    def register_cmpxchg(self, tokens):
        self.rhs = analyze_cmpxchg(tokens)
        node_name = "*{0} = {2} if *{0} = {1}".format(self.rhs.get_address(), self.rhs.get_cmp(), self.rhs.get_new())
        self.register_statement(node_name)

    def register_atomicrmw(self, tokens):
        self.rhs = analyze_atomicrmw(tokens)
        node_name = "{0}; {1}({0}, {2})".format(self.rhs.get_address(), self.rhs.get_operation(), self.rhs.get_value())
        self.register_statement(node_name)

    def register_getelementptr(self, tokens):
        self.rhs = analyze_getelementptr(tokens)
        node_name = "getelementptr {}".format(self.rhs.get_value())
        for idx in self.rhs.get_indices():
            node_name += "[{}]".format(idx)
        self.register_statement(node_name)

    # Analyze Conversion operations
    # -----------------------------
    # register_conversion()

    def register_conversion(self, tokens):
        self.rhs = analyze_conversion(tokens)
        node_name = "{} {} to {}".format(self.rhs.get_operation(), self.rhs.get_value(), self.rhs.get_final_type())
        self.register_statement(node_name)

    # Analyze Other operations
    # ------------------------
    # register_icmp()
    # register_fcmp()
    # register_phi()
    # register_select()
    # register_freeze()
    # register_call()

    def register_cmp(self, tokens):
        self.rhs = analyze_cmp(tokens)
        self.register_statement("{} {} {}".format(self.rhs.get_value1(),
                                                  self.rhs.get_condition(),
                                                  self.rhs.get_value2()))

    def register_phi(self, tokens):
        self.rhs = analyze_phi(tokens)
        node_name = ""
        for option in self.rhs.get_options():
            node_name += "{} if prev= {}".format(option.get_value(), option.get_label())
        self.register_statement(node_name)

    def register_select(self, tokens):
        self.rhs = analyze_select(tokens)
        node_name = "select {} if {} else {}".format(self.rhs.get_val1(), self.rhs.get_condition(), self.rhs.get_val2())
        self.register_statement(node_name)

    def register_freeze(self, tokens):
        self.rhs = analyze_freeze(tokens)
        node_name = "freeze {}".format(self.rhs.get_value())
        self.register_statement(node_name)

    def analyze_call(self, tokens):
        self.rhs = analyze_call(tokens)
        function_name = self.rhs.function_name
        function_call = "call {}".format(function_name)

        if function_name not in self.evaluated_functions and function_name not in self.functions_to_evaluate:
            self.functions_to_evaluate.append(function_name)

        new_node = self.register_statement(function_call)
        self.function_handler.add_call(self.opened_function, new_node)

        for argument in self.rhs.get_arguments():
            argument_node = self.graphs[self.opened_function].add_node(argument.get_register())
            new_node.add_argument(argument_node)

        if function_name in self.top_graph_nodes:
            final_node = self.top_graph_nodes[function_name]
        else:
            final_node = self.top_graph.add_node(function_name)
            self.top_graph_nodes[function_name] = final_node
        first_node = self.top_graph_nodes[self.opened_function]
        self.top_graph.add_edge(first_node, final_node)

        # move the main node to the back of the list, so that the assignment can be handled properly
        index = self.node_stack[self.opened_function].index(new_node)
        self.node_stack[self.opened_function].append(self.node_stack[self.opened_function].pop(index))

    # analyze assignment
    # ------------------
    # assignments are tracked to determine the linkage of variables, and to track value at time of analysis

    def analyze_assignment(self, tokens):
        self.assignee = tokens[0]

    def register_function_end(self):
        self.opened_function = None

    # create a new node, based upon the statement given
    def register_statement(self, statement):
        prev_node = self.node_stack[self.opened_function][-1]

        new_node = self.add_node(statement, self.rhs)
        self.graphs[self.opened_function].add_edge(prev_node, new_node)

        return new_node

    def get_first_node_of_block(self, block_name):
        start = self.graphs[self.opened_function].get_start_of_block(block_name.split(":")[1])
        if start is not None:
            return start
        else:
            self.node_stack[block_name] = list()
            new_node = self.add_node(block_name.split(":")[1])
            self.graphs[self.opened_function].register_start_of_block(block_name.split(":")[1])
            return new_node

    def add_node(self, node_name, context=None):
        new_node = self.graphs[self.opened_function].add_node(node_name)
        new_node.set_context(context)
        self.node_stack[self.opened_function].append(new_node)
        return new_node


class AssignedValue:
    def __init__(self, value, ref=False):
        self.value = value
        self.memory_ref = ref

    def is_reference(self):
        return self.memory_ref

    def __str__(self):
        return self.value
