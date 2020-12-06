from graph.graph import Graph
from yaml import load
import re

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

from llvmAnalyser.function import FunctionHandler
from llvmAnalyser.attributes import AttributeGroupHandler
from llvmAnalyser.testingFramework.gtest import Gtest

from llvmAnalyser.terminator.br import analyze_br
from llvmAnalyser.terminator.switch import analyze_switch
from llvmAnalyser.terminator.indirectbr import analyze_inidrectbr
from llvmAnalyser.terminator.invoke import analyze_invoke
from llvmAnalyser.terminator.callbr import analyze_callbr
from llvmAnalyser.terminator.resume import analyze_resume

from llvmAnalyser.binary.binaryOp import BinaryOpAnalyzer
from llvmAnalyser.binary.fpBinaryOp import FpBinaryOpAnalyzer

from llvmAnalyser.bitwiseBinary.bitwiseBinary import analyze_bitwise_binary

from llvmAnalyser.vector.extractelement import analyze_extractelement
from llvmAnalyser.vector.insertelement import analyze_insertelement
from llvmAnalyser.vector.shufflevector import analyze_shufflevector

from llvmAnalyser.aggregate.insertvalue import analyze_insertvalue
from llvmAnalyser.aggregate.extractvalue import analyze_extractvalue

from llvmAnalyser.memoryAccess.store import analyze_store
from llvmAnalyser.memoryAccess.load import analyze_load
from llvmAnalyser.memoryAccess.cmpxchg import analyze_cmpxchg
from llvmAnalyser.memoryAccess.atomicrmw import analyze_atomicrmw
from llvmAnalyser.memoryAccess.getelementptr import analyze_getelementptr

from llvmAnalyser.conversion.conversion import analyze_conversion

from llvmAnalyser.other.cmp import analyze_cmp
from llvmAnalyser.other.phi import analyze_phi
from llvmAnalyser.other.select import analyze_select
from llvmAnalyser.other.freeze import analyze_freeze
from llvmAnalyser.other.call import CallAnalyzer, Call

from llvmAnalyser.analyzeTestMethod import get_focal_method

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
        self.test_identifier = None
        if self.config["test_framework"] == "gtest":
            self.test_identifier = Gtest

        # make handlers for the specific llvm statements
        self.function_handler = FunctionHandler()
        self.attribute_group_handler = AttributeGroupHandler()

        self.binary_op_analyzer = BinaryOpAnalyzer()
        self.fp_binary_op_analyzer = FpBinaryOpAnalyzer()

        self.call_analyzer = CallAnalyzer()

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
        self.opened_function_memory = None

        # keep track of what register we are assigning to (if any),
        # this is an object of type llvmAnalyser.memory.Register
        self.assignee = None

        # keep track of the rhs value of the assignment
        # this can be of any statement object part of the llvm analyzers
        self.rhs = None

    def analyse(self, file):
        f = open(file, "r")
        lines = f.readlines()
        f.close()

        while len(lines) != 0:
            tokens = list(filter(None, lines[0].replace("\t", "").replace("\n", "").split(";")[0].split(" ")))

            if len(tokens) == 0:
                lines.pop(0)
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
                lines.pop(0)
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
                self.register_return()

            # register br statement
            elif "br" in tokens:
                self.register_br(tokens)

            # register switch statement
            elif "switch" in tokens:
                for _ in range(3):
                    tokens += list(filter(None, lines[1].replace("\t", "").replace("\n", "").split(" ")))
                    lines.pop(1)
                self.register_switch(tokens)

            # register indirectbr statement
            elif "indirectbr" in tokens:
                self.register_indirectbr(tokens)

            # register invoke statement
            elif "invoke" in tokens:
                tokens += list(filter(None, lines[1].replace("\t", "").replace("\n", "").split(" ")))
                lines.pop(1)
                self.register_invoke(tokens)

            # register callbr statement
            elif "callbr" in tokens:
                self.register_callbr(tokens)

            # register resume statement
            elif "resume" in tokens:
                self.register_resume(tokens)

            # skip catchswitch
            elif "catchswitch" in tokens:
                lines.pop(0)
                continue

            # skip catchret
            elif "catchret" in tokens:
                lines.pop(0)
                continue

            # skip cleanupret
            elif "cleanupret" in tokens:
                lines.pop(0)
                continue

            # register unreachable statement
            elif "unreachable" in tokens:
                self.register_unreachable()

            # Binary operations
            # -----------------
            # Binary operations are used for most computations in a program. They require two operands of the same type
            # and it results in a single value on which the operation is applied.
            # The binary operators are split into two main categories,
            #   operations on integer or vector of integer values, simply referred to as binary operations
            #   operations on floating-point or vector of floating-point values, referred to as floating-point binary
            #       operations

            # register binary integer operation
            elif len(tokens) > 2 and tokens[2] in ["add", "sub", "mul", "sdiv", "srem", "udiv", "urem"]:
                self.register_binary_op(tokens)

            # register binary floating point operations
            elif len(tokens) > 2 and tokens[2] in ["fadd", "fsub", "fmul", "fdiv"]:
                self.register_fp_binary_op(tokens)

            # Bitwise binary operations
            # -------------------------
            # Bitwise binary operations are used to do various forms of bit-twiddling in a program. They require two
            # operands of the same type, execute an operation on them, and produce a single value. The following
            # bitwise binary operations exist within llvm:
            #   'sh1', 'lshr', 'ashr', 'and', 'or', 'xor'

            # register bitwise binary instruction
            elif len(tokens) > 2 and tokens[2] in ["sh1", "lshr", "ashr", "and", "or", "xor"]:
                self.register_bitwise_binary(tokens)

            # Vector operations
            # -----------------
            # Vector operations cover element-access and vector-specific operations needed to process vectors
            # effectively.
            # The vector instructions are:
            #   'extractelement', 'insertelement', 'shufflevector'

            # register extractelement statement
            elif "extractelement" in tokens:
                self.register_extractelement(tokens)

            # register insertelement statement
            elif "insertelement" in tokens:
                self.register_insertelement(tokens)

            # register shufflevector statement
            elif "shufflevector" in tokens:
                self.register_shufflevector(tokens)

            # Aggregate Operations
            # --------------------
            # Aggregate operations are instructions that allow us to work with aggregate values.
            # The aggregate instructions are:
            #   'extractvalue', 'insertvalue'

            # register extractvalue statement
            elif "extractvalue" in tokens:
                self.register_extractvalue(tokens)

            # register insertvalue statement
            elif "insertvalue" in tokens:
                self.register_insertvalue(tokens)

            # Memory Access and Addressing operations
            # ---------------------------------------
            # The following operations are used to read, write and allocate memory in LLVM:
            #   'alloca, 'load', 'store', 'fence', 'cmpxchg', 'atomicrmw', 'getelementptr'

            # register alloca statement
            elif "alloca" in tokens:
                self.assignee = None
                lines.pop(0)
                continue

            # register load statement
            elif "load" in tokens:
                self.register_load(tokens)

            # register store statement
            elif "store" in tokens:
                self.register_store(tokens)

            # register fence statement
            elif "fence" in tokens:
                lines.pop(0)
                continue

            # register cmpxchg statement
            elif "cmpxchg" in tokens:
                self.register_cmpxchg(tokens)

            # register atomicrmx statement
            elif "atomicrmw" in tokens:
                self.register_atomicrmw(tokens)

            # register getelementptr statement
            elif len(tokens) > 2 and tokens[2] == "getelementptr":
                self.register_getelementptr(tokens)

            # Conversion operations
            # ---------------------
            # Conversion operations allow the casting of variables, the following conversion operations are defined
            # within LLVM:
            #   'trunc .. to', 'zext .. to', 'sext .. to', 'fptrunc .. to', 'fpext .. to',
            #   'fptoui .. to', 'fptosi .. to', 'uitofp .. to', 'sitofp .. to',
            #   'ptrtoint .. to', 'inttoptr .. to', 'bitcast .. to', 'addrspacecast .. to'

            # register conversion statement
            elif len(tokens) > 2 and tokens[2] in ["trunc", "zext",     "sext",     "fptrunc",
                                                   "fpext", "fptoui",   "fptosi",   "uitofp",
                                                   "sitofp", "ptrtoint", "inttoptr", "bitcast",
                                                   "addrspacecast"]:
                self.register_conversion(tokens)

            # other operations
            # ----------------
            # The other instructions are specified as other, due to lack of better classification. These are general
            # cross operation set operations. The llvm instruction set contains the following operations of type other:
            #   'icmp', 'fcmp', 'phi', 'select', 'freeze', 'call', 'va_arg', 'landingpad', 'catchpad', 'cleanuppad'

            # register icmp statement
            elif len(tokens) > 2 and tokens[2] in ["icmp", "fcmp"]:
                self.register_cmp(tokens)

            # register phi statement
            elif "phi" in tokens:
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
                    if "catch" in lines[1]:
                        lines.pop(1)
                    elif "cleanup" in lines[1]:
                        lines.pop(1)
                    elif "filter" in lines[1]:
                        lines.pop(1)
                    else:
                        break

                self.assignee = None
                lines.pop(0)
                continue

            # register catchpad statement
            elif "catchpad" in tokens:
                self.assignee = None
                lines.pop(0)
                continue

            # register clenuppad statement
            elif "cleanuppad" in tokens:
                self.assignee = None
                lines.pop(0)
                continue

            # register new code block
            elif block_start_format.match(tokens[0]):
                opened_block = "{}:%{}".format(self.opened_function, tokens[0].split(":")[0])
                self.node_stack[self.opened_function].append(self.get_first_node_of_block(opened_block))

            # register end of function definition
            elif tokens[0] == "}":
                self.register_function_end()

            elif self.opened_function is not None:
                print("Error: unregistered instruction!")
                print(tokens)
                print(lines[0])

            if self.assignee is not None:
                new_name = "{} = {}".format(self.assignee, self.node_stack[self.opened_function][-1].get_name())
                top_node = self.node_stack[self.opened_function][-1]
                top_node.set_name(new_name)
                self.opened_function_memory.assign_value_to_reg(self.assignee, self.rhs)
                self.opened_function_memory.add_node_to_reg(self.assignee, top_node)

                self.rhs = None
                self.assignee = None

            lines.pop(0)

        # get the list of functions used for assertions
        assert_helpers = self.top_graph.check_for_assert_helpers()

        # keep track of the functions under test for each test function
        focal_methods = dict()

        # iterate over all defined graphs
        for graph in self.graphs:
            # we only want to draw test functions
            if self.graphs[graph].is_test_func():
                # make an entry in the focal methods dict
                focal_methods[graph] = set()

                # get the memory block of said function
                function_memory = self.function_handler.get_function_memory(graph)

                # get all variables compared in assertions
                assertions = self.graphs[graph].check_for_used_assertion(assert_helpers)

                # call the get_focal_method function for each parameter of the assertions
                for assertion in assertions:
                    for parameter in assertion.get_arguments():
                        get_focal_method(assertion, parameter)

                # trace where said variables are used, in case they can be traced back to a call
                # return said register, if not, return None
                # we want to track all initial calls, as these are considered to be functions under test
                # initial_vars = list()
                # for test_var in test_vars:
                #     initial = self.check_for_initial_call(str(test_var).split("\"")[1], function_memory)
                #     if initial is not None:
                #         initial_vars.append(initial)

                # set all initial nodes as test variables in the graph
                # for initial_var in initial_vars:
                #     node = function_memory.get_node(initial_var)
                #     node.set_test_var()
                #     self.top_graph_nodes[node.get_context().get_function_name()].set_test_var()
                #     focal_methods[graph].add(node.get_context().get_function_name())

                # draw the relevant graphs if desired
                if self.config["graph"]:
                    self.graphs[graph].export_graph(graph)

        # draw the top graph if desired
        if self.config["graph"]:
            self.top_graph.export_graph("top_level_graph")

        return focal_methods

    def analyze_define(self, tokens):
        self.opened_function = self.function_handler.identify_function(tokens)
        self.opened_function_memory = self.function_handler.get_function_memory(self.opened_function)
        self.graphs[self.opened_function] = Graph()
        self.node_stack[self.opened_function] = list()
        new_node = self.add_node(self.opened_function)
        if self.opened_function not in self.top_graph_nodes:
            top_graph_node = self.top_graph.add_node(self.opened_function)
            self.top_graph_nodes[self.opened_function] = top_graph_node
        if self.test_identifier.identify_test_function(self.opened_function):
            self.top_graph_nodes[self.opened_function].set_test()
            self.graphs[self.opened_function].set_test_func()
            new_node.set_test()
        if self.test_identifier.identify_assertion_function(self.opened_function):
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

    def register_return(self):
        prev_node = self.node_stack[self.opened_function][-1]
        new_node = self.add_node("ret")
        new_node.set_final()
        self.graphs[self.opened_function].add_edge(prev_node, new_node)

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
        new_node = self.register_statement(self.rhs.get_func())

        block_name = "{}:{}".format(self.opened_function, self.rhs.get_normal())
        normal_node = self.get_first_node_of_block(block_name)
        self.graphs[self.opened_function].add_edge(new_node, normal_node, "normal")

        block_name = "{}:{}".format(self.opened_function, self.rhs.get_exception())
        exception_node = self.get_first_node_of_block(block_name)
        self.graphs[self.opened_function].add_edge(new_node, exception_node, "exception")

    def register_callbr(self, tokens):
        self.rhs = analyze_callbr(tokens)
        prev_node = self.node_stack[self.opened_function][-1]

        function_name = self.rhs.get_function_name()

        new_node = self.add_node("call {}".format(function_name), self.rhs)

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

    def register_resume(self, tokens):
        self.rhs = analyze_resume(tokens)
        node_name = "resume {} {}".format(self.rhs.get_type(), self.rhs.get_type())
        self.register_statement(node_name)

    def register_unreachable(self):
        prev_node = self.node_stack[self.opened_function][-1]

        new_node = self.add_node("unreachable")
        self.graphs[self.opened_function].add_edge(prev_node, new_node)

    # Analyze Binary operations
    # -------------------------
    # register_binary_op()
    # register_fp_binary_op()

    def register_binary_op(self, tokens):
        self.rhs = self.binary_op_analyzer.analyze_binary_op(tokens)
        node_name = "{} {} {}".format(self.rhs.get_value1(), self.rhs.get_op(), self.rhs.get_value2())
        self.register_statement(node_name)

    def register_fp_binary_op(self, tokens):
        self.rhs = self.fp_binary_op_analyzer.analyze_fp_binary_op(tokens)
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
        new_node = self.register_statement("{} = {}".format(self.rhs.get_register(), str(self.rhs.get_value())))

        self.opened_function_memory.assign_value_to_reg(self.rhs.get_register(), self.rhs.get_value())
        self.opened_function_memory.add_node_to_reg(self.rhs.get_register(), new_node)

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
        self.rhs = self.call_analyzer.analyze_call(tokens)
        function_name = self.rhs.function_name
        function_call = "call {}".format(function_name)

        new_node = self.register_statement(function_call)

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

    # analyze assignment
    # ------------------
    # assignments are tracked to determine the linkage of variables, and to track value at time of analysis

    def analyze_assignment(self, tokens):
        self.assignee = tokens[0]

    def register_function_end(self):
        self.opened_function_memory = None
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

    # we need to determine what values correspond to the registers used for testing
    # we will trace the assigned values to registers throughout the function
    # when it halts at a constant, we stop our trace, and assume that this is a value that is used
    # to compare against, and not the value under test
    # in case we encounter a function, we return the first register that is used
    @staticmethod
    def check_for_initial_call(token, memory):
        current = [token]
        new = list()

        while True:
            while current:
                new_token = current.pop(0)

                # assigned by instruction we skipped, therefore assumed to be irrelevant
                if not memory.is_reg_in_mem(new_token):
                    continue

                next_rhs = memory.get_val(new_token)
                if isinstance(next_rhs, Call):
                    return new_token

                used_var = next_rhs.get_used_variables()
                if used_var is not None:
                    new += used_var

            if not new:
                return None

            current = new
            new = list()
