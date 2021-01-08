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

from llvmAnalyser.unary.fneg import analyze_fneg, Fneg

from llvmAnalyser.binary.binaryOp import BinaryOpAnalyzer, BinOp

from llvmAnalyser.bitwiseBinary.bitwiseBinary import analyze_bitwise_binary

from llvmAnalyser.vector.extractelement import analyze_extractelement, ExtractElement
from llvmAnalyser.vector.insertelement import analyze_insertelement, InsertElement
from llvmAnalyser.vector.shufflevector import analyze_shufflevector, Shufflevector

from llvmAnalyser.aggregate.insertvalue import analyze_insertvalue
from llvmAnalyser.aggregate.extractvalue import analyze_extractvalue

from llvmAnalyser.memoryAccess.store import analyze_store, Store
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
        self.test_identifier = re.compile(r'{}'.format(self.config["test_function_signature"]))
        self.assertion_identifier = re.compile(r'{}'.format(self.config["assertion_function_signature"]))
        self.exclusion_filter = re.compile(r'{}'.format(self.config["exclusion_filter"]))

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

        # keep track of the used statements, this will be tracked for each function separately
        self.stores = dict()
        self.loads = dict()
        self.references = dict()
        self.assignments = dict()
        self.returns = dict()
        self.called_functions = dict()

        # keep track of the found mutation types for the functions
        # it will be tracked per function, and per argument of said function
        self.found_mutation_types = dict()

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

            # get the assertions used within the test function
            assertions = self.get_assertions(function)

            # skip all test helper functions
            if len(assertions) == 0:
                continue

            focal_methods[function] = set()
            self.opened_function = function

            # look if the assertion has a corresponding focal method by calling the get_focal_method
            # function for each of the parameters of the assertion
            # not every assertion is guaranteed to lead to focal methods as some assertions might directly depend
            # on other assertions and not tested variables
            for assertion in assertions:
                arguments = assertion.get_arguments()
                for i in range(len(arguments)):
                    if self.assertion_identifier.match(assertion.get_context().get_arguments()[i].get_parameter_type()):
                        continue

                    for inc in assertion.get_incs():
                        methods = self.find_focal_methods(arguments[i].get_name(), inc)
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
    # to prevent issues regarding recursion depth, this function will go breadth first with an iterative approach
    def find_focal_methods(self, test_var, test_node):
        focal_methods = set()
        checked_states = dict()

        # setup for the first iteration, in the first iteration it will just contain the assertion, alongside the
        # tracked variable within said assertion
        current_iteration = list()
        current_iteration.append((test_var, test_node, False, 0))
        max_depth = float("inf")
        mutator_method = None

        # setup a tracker that tracks all variables for the next iteration, at the end of an iteration, we
        # move the tracker to the current iteration, and we clear the tracker so that it can track sets for the next
        next_iteration = list()

        # store the root, this needs to be done as we want to be able to start over, in case it turns out that
        # a new variable contains our test variable, in that case, every mutation that we might have passed on our
        # way to the current node, might actually have been the mutation of our test case
        root = test_node

        # while there are variables left to track
        while current_iteration:

            # iterate over all (var, node) pairs stored for the current iteration
            for test_var, test_node, contains, depth in current_iteration:
                # check if the current state is registered within the checked states dictionary
                if test_node not in checked_states:
                    checked_states[test_node] = set()

                # check if we are dealing with a non variable
                if test_var[0] not in {"%", "@"}:
                    continue

                # detect a loop, if no loop, register that we are currently investigating the tracked variable
                if test_var in checked_states[test_node]:
                    continue
                else:
                    checked_states[test_node].add(test_var)

                # capture the relevant data from the node
                context = test_node.get_context()
                node_name = test_node.get_name()

                # track some attributes of our current node
                test_is_arg = False
                test_is_assignee = False
                is_func_call = False

                # if we are dealing with an assignment, track which variable we are assigning to
                assignee = None

                # these will only be set in case we encounter a function call
                arguments = None
                function_name = None
                is_defined = False
                is_excluded = False
                is_intrinsic = False

                # verify whether or not a function was used
                if isinstance(context, (Call, Invoke, CallBr)):

                    # register that our context is indeed a function call
                    is_func_call = True
                    arguments = context.get_arguments()
                    function_name = context.get_function_name()

                    if function_name in self.node_stack:
                        is_defined = True

                    if re.match(r'@llvm\.(memcpy|memset|memmove).*', function_name):
                        is_intrinsic = True
                        is_excluded = True

                    # if the current context is another assertion related function, we can just carry on
                    # as its respective used variables will be evaluated in a separate evaluation
                    if self.assertion_identifier.match(function_name):
                        for inc in test_node.get_incs():
                            next_iteration.append((test_var, inc, contains, depth + 1))
                        continue

                    # check if our test var is one of the arguments of the function
                    args = context.get_arguments()
                    for arg in args:
                        if arg.get_register() == test_var:
                            test_is_arg = True
                            if arg.is_ret_var():
                                test_is_assignee = True
                            break

                    # check if our function is an excluded function
                    if self.exclusion_filter.pattern != "" and self.exclusion_filter.match(function_name):
                        is_excluded = True

                # verify whether or not an assignment occurred
                if re.match(r'^%\d*? = .*?$', node_name):

                    # if the test var is the assignee, we need to consider all used variables in the rhs as being
                    # potential variables used in the mutation of our test var
                    assignee = node_name.split(" = ")[0]
                    if assignee == test_var:
                        test_is_assignee = True

                # if we called a function in which our test var could potentially get mutated,
                # we mark it as focal method, and we carry on with subsequent nodes
                if is_func_call and not is_defined and not is_excluded and (test_is_arg or test_is_assignee):
                    if max_depth == float("inf"):
                        focal_methods.add(function_name)
                    if test_is_assignee:
                        for argument in arguments:
                            reg = argument.get_register()
                            if reg != test_var:
                                next_iteration.append((reg, root, argument.is_pointer(), 0))

                # if we called a function, and its return is assigned to our test var or
                # the test var is used as one of its arguments, track all used variables as potential extended test var
                if is_func_call and is_defined and not is_excluded and (test_is_arg or test_is_assignee):
                    callee_attributes = self.function_handler.get_function_arguments(function_name)

                    if not test_is_assignee:
                        callee_attributes = [callee_attributes[context.get_argument_registers().index(test_var)]]

                    for i in range(len(callee_attributes)):
                        callee_attribute = callee_attributes[i]

                        reg = callee_attribute.get_register()

                        temp = self.opened_function
                        self.opened_function = function_name

                        if self.opened_function in self.found_mutation_types:
                            if reg in self.found_mutation_types[self.opened_function]:
                                if False in self.found_mutation_types[self.opened_function][reg]:
                                    mutator = self.found_mutation_types[self.opened_function][reg][False]
                                else:
                                    self.found_mutation_types[self.opened_function][reg][False] = "inspector"
                                    mutator, _ = self.is_arg_mutated(reg, callee_attribute.is_pointer())
                                    self.found_mutation_types[self.opened_function][reg][False] = mutator
                            else:
                                self.found_mutation_types[self.opened_function][reg] = dict()
                                self.found_mutation_types[self.opened_function][reg][False] = "inspector"
                                mutator, _ = self.is_arg_mutated(reg, callee_attribute.is_pointer())
                                self.found_mutation_types[self.opened_function][reg][False] = mutator
                        else:
                            self.found_mutation_types[self.opened_function] = dict()
                            self.found_mutation_types[self.opened_function][reg] = dict()
                            self.found_mutation_types[self.opened_function][reg][False] = "inspector"
                            mutator, _ = self.is_arg_mutated(reg, callee_attribute.is_pointer())
                            self.found_mutation_types[self.opened_function][reg][False] = mutator

                        self.opened_function = temp

                        if mutator == "mutator" and depth < max_depth:
                            mutator_method = function_name
                            max_depth = depth
                        elif mutator == "uncertain" and max_depth == float("inf"):
                            focal_methods.add(function_name)

                    for i in range(len(arguments)):
                        reg = arguments[i].get_register()
                        if reg != test_var and not self.assertion_identifier.match(arguments[i].get_parameter_type()):
                            next_iteration.append((reg, root, arguments[i].is_pointer(), 0))

                if is_func_call and is_excluded and (test_is_arg or test_is_assignee):
                    for i in range(len(arguments)):
                        reg = arguments[i].get_register()
                        if reg != test_var and not self.assertion_identifier.match(arguments[i].get_parameter_type()):
                            next_iteration.append((reg, root, arguments[i].is_pointer(), 0))

                # if we assigned to our test_variable and we are not considering a call, we still have to consider
                # the used variables in the rhs as possible test targets
                if test_is_assignee and not is_func_call:
                    for var in context.get_used_variables():
                        next_iteration.append((var, root, False, 0))

                # check if our variable was assigned to a reference, in that case, the object from which it is a
                # reference now contains our variable under tests, and is therefore also a variable under test
                if isinstance(context, Store):
                    if test_var == context.get_value():
                        if assignee in self.references[self.opened_function]:
                            next_iteration.append((self.references[self.opened_function][assignee], root, True, 0))

                # check if we loaded a reference of our test var that contains a reference to our original test var
                if isinstance(context, Load) and contains:
                    loaded_var = context.get_value()
                    for lhs, rhs in self.references[self.opened_function].items():
                        if rhs == test_var and lhs == loaded_var:
                            next_iteration.append((assignee, root, False, 0))

                # check if we created a reference of our test var
                if isinstance(context, Getelementptr) and context.get_value() == test_var:
                    next_iteration.append((assignee, root, contains, 0))

                # check if we casted a variable that contained our original test var to a var of different type
                if isinstance(context, Conversion) and context.get_value() == test_var:
                    next_iteration.append((assignee, root, contains, 0))

                # check if we called an intrinsic memory move function upon a variable that contained our
                # original test var
                if is_func_call and is_intrinsic:
                    if arguments[1].get_register() == test_var and contains:
                        next_iteration.append((arguments[0].get_register(), root, True, 0))

                # if there are any subsequent nodes, keep on traversing using our currently considered test var
                for inc in test_node.get_incs():
                    next_iteration.append((test_var, inc, contains, depth + 1))

            current_iteration = next_iteration
            next_iteration = list()

        if mutator_method is not None:
            focal_methods.add(mutator_method)
        return focal_methods

    # see if an argument of a function is mutated within that function scope
    def is_arg_mutated(self, var, ref=False, recursion_depth=1):
        mutation_type = "inspector"
        returns_ref = False

        current_iteration = list()
        current_iteration.append((var, ref))

        next_iteration = list()

        encountered = dict()

        while current_iteration:
            for tracked_variable, is_ref in current_iteration:
                if tracked_variable in encountered and is_ref in encountered[tracked_variable]:
                    continue
                elif tracked_variable in encountered:
                    encountered[tracked_variable].append(is_ref)
                else:
                    encountered[tracked_variable] = list()

                # this means the function was never analysed, and was therefore not defined
                # in case it was defined, but below the max depth, our current depth will be equal to the
                # max depth, and we will not consider the function as being uncertain
                if self.opened_function not in self.node_stack and recursion_depth < self.config["max_depth"]:
                    return "uncertain", False

                used_functions = self.function_handler.get_used_functions(self.opened_function)

                for used_function in used_functions:
                    context = used_function.get_context()
                    func_name = context.get_function_name()
                    intrinsic_functions = r'@llvm\.(memcopy|memset|memmove).*'
                    arg_regs = context.get_argument_registers()
                    if tracked_variable in arg_regs and func_name in self.node_stack:
                        temp = self.opened_function
                        self.opened_function = context.get_function_name()
                        index = context.get_argument_registers().index(tracked_variable)
                        function = self.function_handler.get_function(self.opened_function)
                        new_function_args = function.get_argument_registers()
                        new_var = new_function_args[index]

                        if self.opened_function in self.found_mutation_types:
                            if new_var in self.found_mutation_types[self.opened_function]:
                                if is_ref in self.found_mutation_types[self.opened_function][new_var]:
                                    mut = self.found_mutation_types[self.opened_function][new_var][is_ref]
                                else:
                                    self.found_mutation_types[self.opened_function][new_var][is_ref] = "inspector"
                                    mut, ref = self.is_arg_mutated(new_var, is_ref, recursion_depth + 1)
                                    self.found_mutation_types[self.opened_function][new_var][is_ref] = mut
                            else:
                                self.found_mutation_types[self.opened_function][new_var] = dict()
                                self.found_mutation_types[self.opened_function][new_var][is_ref] = "inspector"
                                mut, ref = self.is_arg_mutated(new_var, is_ref, recursion_depth + 1)
                                self.found_mutation_types[self.opened_function][new_var][is_ref] = mut
                        else:
                            self.found_mutation_types[self.opened_function] = dict()
                            self.found_mutation_types[self.opened_function][new_var] = dict()
                            self.found_mutation_types[self.opened_function][new_var][is_ref] = "inspector"
                            mut, ref = self.is_arg_mutated(new_var, is_ref, recursion_depth + 1)
                            self.found_mutation_types[self.opened_function][new_var][is_ref] = mut

                        self.opened_function = temp

                        if mut == "mutator":
                            return "mutator", False
                        elif mut == "uncertain":
                            mutation_type = "uncertain"

                    elif len(arg_regs) > 0 and tracked_variable == arg_regs[0] and \
                            re.match(intrinsic_functions, func_name):
                        return "mutator", False

                    elif tracked_variable in arg_regs and func_name not in self.node_stack and \
                            recursion_depth + 1 < self.config["max_depth"]:
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
                    return "mutator", False

                for lhs, rhs in self.stores[self.opened_function].items():
                    # this means that we assigned our tracked variable to a dif variable
                    if rhs == tracked_variable:
                        next_iteration.append((lhs, is_ref))

                for lhs, rhs in self.loads[self.opened_function].items():
                    # this means that we loaded our tracked variable into a dif variable
                    if rhs.get_value() == tracked_variable:
                        next_iteration.append((lhs, rhs.returns_pointer()))

                for lhs, rhs in self.assignments[self.opened_function].items():
                    # this means that we converted our tracked variable to a dif type
                    if rhs == tracked_variable:
                        next_iteration.append((lhs, is_ref))

                for var, ref in self.references[self.opened_function].items():
                    # this means that we assigned a reference of our tracked variable to a dif variable
                    if ref == tracked_variable:
                        next_iteration.append((var, True))

                for var, context in self.called_functions[self.opened_function].items():
                    # this means that we assigned the result of a call to a dif variable
                    if tracked_variable in context.get_used_variables():
                        next_iteration.append((var, context.returns_pointer()))

                # this means that we returned a reference to a tracked variable
                if tracked_variable in self.returns[self.opened_function]:
                    returns_ref = is_ref

            current_iteration = next_iteration
            next_iteration = list()

        return mutation_type, returns_ref

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
                    self.loads[self.opened_function][self.assignee] = self.rhs

                elif isinstance(self.rhs, Getelementptr):
                    self.references[self.opened_function][self.assignee] = self.rhs.get_value()

                elif isinstance(self.rhs, (Conversion, Fneg)):
                    self.assignments[self.opened_function][self.assignee] = self.rhs.get_value()

                elif isinstance(self.rhs, (ExtractElement, InsertElement, Shufflevector)):
                    self.assignments[self.opened_function][self.assignee] = self.rhs.get_vector_value()

                elif isinstance(self.rhs, BinOp):
                    self.assignments[self.opened_function][self.assignee] = self.rhs.get_value1()
                    self.assignments[self.opened_function][self.assignee] = self.rhs.get_value2()

                elif isinstance(self.rhs, (Call, CallBr, Invoke)):
                    self.called_functions[self.opened_function][self.assignee] = self.rhs

                self.rhs = None
                self.assignee = None

            i += 1

        return

    def analyze_define(self, tokens):
        self.opened_function = self.function_handler.identify_function(tokens)
        self.stores[self.opened_function] = dict()
        self.loads[self.opened_function] = dict()
        self.references[self.opened_function] = dict()
        self.assignments[self.opened_function] = dict()
        self.returns[self.opened_function] = list()
        self.called_functions[self.opened_function] = dict()
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
            self.returns[self.opened_function].append(self.rhs.get_value())
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
            node_name += ", {} if prev= {}".format(option.get_value(), option.get_label())
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
