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

from llvmAnalyser.bitwiseBinary.bitwiseBinary import BitwiseBinaryAnalyzer

from llvmAnalyser.vector.extractelement import analyze_extractelement
from llvmAnalyser.vector.insertelement import analyze_insertelement

from llvmAnalyser.aggregate.insertvalue import InsertvalueAnalyzer
from llvmAnalyser.aggregate.extractvalue import ExtractvalueAnalyzer

from llvmAnalyser.memoryAccess.store import StoreAnalyzer
from llvmAnalyser.memoryAccess.load import LoadAnalyzer
from llvmAnalyser.memoryAccess.getelementptr import GetelementptrAnalyzer

from llvmAnalyser.conversion.trunc import TruncAnalyzer
from llvmAnalyser.conversion.fpext import FpextAnalyzer
from llvmAnalyser.conversion.sitofp import SitofpAnalyzer
from llvmAnalyser.conversion.bitcast import BitcastAnalyzer

from llvmAnalyser.other.icmp import IcmpAnalyzer
from llvmAnalyser.other.fcmp import FcmpAnalyzer
from llvmAnalyser.other.phi import PhiAnalyzer
from llvmAnalyser.other.call import CallAnalyzer, Call

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

        self.bitwise_binary_analyzer = BitwiseBinaryAnalyzer()

        self.insertvalue_analyzer = InsertvalueAnalyzer()
        self.extractvalue_analyzer = ExtractvalueAnalyzer()

        self.store_analyzer = StoreAnalyzer()
        self.load_analyzer = LoadAnalyzer()
        self.getelementptr_analyzer = GetelementptrAnalyzer()

        self.trunc_analyzer = TruncAnalyzer()
        self.fpext_analyzer = FpextAnalyzer()
        self.sitofp_analayzer = SitofpAnalyzer()
        self.bitcast_analyzer = BitcastAnalyzer()

        self.icmp_analyzer = IcmpAnalyzer()
        self.fcmp_analyzer = FcmpAnalyzer()
        self.phi_analyzer = PhiAnalyzer()
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
            elif "br" in tokens and self.opened_function is not None:
                self.register_br(tokens)

            # register switch statement
            elif "switch" in tokens and self.opened_function is not None:
                for _ in range(3):
                    tokens += list(filter(None, lines[1].replace("\t", "").replace("\n", "").split(" ")))
                    lines.pop(1)
                self.register_switch(tokens)

            # register indirectbr statement
            elif "indirectbr" in tokens and self.opened_function is not None:
                self.register_indirectbr(tokens)

            # register invoke statement
            elif "invoke" in tokens and self.opened_function is not None:
                tokens += list(filter(None, lines[1].replace("\t", "").replace("\n", "").split(" ")))
                lines.pop(1)
                self.register_invoke(tokens)

            # register callbr statement
            elif "callbr" in tokens and self.opened_function is not None:
                self.register_callbr(tokens)

            # register resume statement
            elif "resume" in tokens and self.opened_function is not None:
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
            elif "unreachable" in tokens and self.opened_function is not None:
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
            elif len(tokens) > 2 and tokens[2] in ["add", "sub", "mul", "sdiv", "srem", "udiv", "urem"] and \
                    self.opened_function is not None:
                self.analyze_binary_op(tokens)

            # register binary floating point operations
            elif len(tokens) > 2 and tokens[2] in ["fadd", "fsub", "fmul", "fdiv"] and self.opened_function is not None:
                self.analyze_fp_binary_op(tokens)

            # Bitwise binary operations
            # -------------------------
            # Bitwise binary operations are used to do various forms of bit-twiddling in a program. They require two
            # operands of the same type, execute an operation on them, and produce a single value. The following
            # bitwise binary operations exist within llvm:
            #   'sh1', 'lshr', 'ashr', 'and', 'or', 'xor'

            # register bitwise binary instruction
            elif len(tokens) > 2 and tokens[2] in ["sh1", "lshr", "ashr", "and", "or", "xor"] and \
                    self.opened_function is not None:
                self.analyze_bitwise_binary(tokens)

            # Vector operations
            # -----------------
            # Vector operations cover element-access and vector-specific operations needed to process vectors
            # effectively.
            # The vector instructions are:
            #   'extractelement', 'insertelement', 'shufflevector'

            # register extractelement statement
            elif "extractelement" in tokens and self.opened_function is not None:
                self.register_extractelement(tokens)

            # register insertelement statement
            elif "insertelement" in tokens and self.opened_function is not None:
                self.register_insertelement(tokens)

            # Aggregate Operations
            # --------------------
            # Aggregate operations are instructions that allow us to work with aggregate values.
            # The aggregate instructions are:
            #   'extractvalue', 'insertvalue'

            # register extractvalue statement
            elif "extractvalue" in tokens and self.opened_function is not None:
                self.analyze_extractvalue(tokens)

            # register insertvalue statement
            elif "insertvalue" in tokens and self.opened_function is not None:
                self.analyze_insertvalue(tokens)

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
            elif "load" in tokens and self.opened_function is not None:
                self.analyze_load(tokens)

            # register store statement
            elif "store" in tokens and self.opened_function is not None:
                self.analyze_store(tokens)

            # register getelementptr statement
            elif len(tokens) > 2 and tokens[2] == "getelementptr" and self.opened_function is not None:
                self.analyze_getelementptr(tokens)

            # Conversion operations
            # ---------------------
            # Conversion operations allow the casting of variables, the following conversion operations are defined
            # within LLVM:
            #   'trunc .. to', 'zext .. to', 'sext .. to', 'fptrunc .. to', 'fpext .. to',
            #   'fptoui .. to', 'fptosi .. to', 'uitofp .. to', 'sitofp .. to',
            #   'ptrtoint .. to', 'inttoptr .. to', 'bitcast .. to', 'addrspacecast .. to'

            # register trunc .. to statement
            elif len(tokens) > 2 and tokens[2] == "trunc" and self.opened_function is not None:
                self.analyze_trunc(tokens)

            # register fpext .. to statement
            elif len(tokens) > 2 and tokens[2] == "fpext" and self.opened_function is not None:
                self.analyze_fpext(tokens)

            # register sitofp .. to statement
            elif len(tokens) > 2 and tokens[2] == "sitofp" and self.opened_function is not None:
                self.analyze_sitofp(tokens)

            # register bitcast statement
            elif "bitcast" in tokens and self.opened_function is not None:
                self.analyze_bitcast(tokens)

            # other operations
            # ----------------
            # The other instructions are specified as other, due to lack of better classification. These are general
            # cross operation set operations. The llvm instruction set contains the following operations of type other:
            #   'icmp', 'fcmp', 'phi', 'select', 'freeze', 'call', 'va_arg', 'landingpad', 'catchpad', 'cleanuppad'

            # register icmp statement
            elif "icmp" in tokens and self.opened_function is not None:
                self.analyze_icmp(tokens)

            # register fcmp statement
            elif "fcmp" in tokens and self.opened_function is not None:
                self.analyze_fcmp(tokens)

            # register phi statement
            elif "phi" in tokens and self.opened_function is not None:
                self.analyze_phi(tokens)

            # register function call
            elif "call" in tokens and self.opened_function is not None:
                self.analyze_call(tokens)

            # register landingpad statement
            elif "landingpad" in tokens and self.opened_function is not None:
                while True:
                    if "catch" in lines[1]:
                        lines.pop(1)
                    elif "cleanup" in lines[1]:
                        lines.pop(1)
                    elif "filter" in lines[1]:
                        lines.pop(1)
                    else:
                        break

                self.analyze_landingpad()
                lines.pop(0)
                continue

            # register new code block
            elif block_start_format.match(tokens[0]) and self.opened_function is not None:
                opened_block = "{}:%{}".format(self.opened_function, tokens[0].split(":")[0])
                self.node_stack[self.opened_function].append(self.get_first_node_of_block(opened_block))

            # register end of function definition
            elif tokens[0] == "}":
                self.register_function_end()

            elif self.opened_function is not None:
                print("Error: unregistered instruction!")
                print(tokens)

            if self.assignee is not None:
                if self.opened_function is not None:
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
                test_vars = self.graphs[graph].check_for_used_assertion(assert_helpers)

                # trace where said variables are used, in case they can be traced back to a call
                # return said register, if not, return None
                # we want to track all initial calls, as these are considered to be functions under test
                initial_vars = list()
                for test_var in test_vars:
                    initial = self.check_for_initial_call(str(test_var).split("\"")[1], function_memory)
                    if initial is not None:
                        initial_vars.append(initial)

                # set all initial nodes as test variables in the graph
                for initial_var in initial_vars:
                    node = function_memory.get_node(initial_var)
                    node.set_test_var()
                    self.top_graph_nodes[node.get_context().get_function_name()].set_test_var()
                    focal_methods[graph].add(node.get_context().get_function_name())

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
    # analyze_binary_op()
    # analyze_fp_binary_op()

    def analyze_binary_op(self, tokens):
        self.rhs = self.binary_op_analyzer.analyze_binary_op(tokens)
        node_name = "{} {} {}".format(self.rhs.get_value1(), self.rhs.get_op(), self.rhs.get_value2())
        self.register_statement(node_name)

    def analyze_fp_binary_op(self, tokens):
        self.rhs = self.fp_binary_op_analyzer.analyze_fp_binary_op(tokens)
        node_name = "{} {} {}".format(self.rhs.get_value1(), self.rhs.get_op(), self.rhs.get_value2())
        self.register_statement(node_name)

    # Analyze Bitwise Binary operations
    # ---------------------------------
    # analyze_xor()

    def analyze_bitwise_binary(self, tokens):
        self.rhs = self.bitwise_binary_analyzer.analyze_bitwise_binary(tokens)
        node_name = "{} {} {}".format(self.rhs.op1, self.rhs.get_statement_type(), self.rhs.op2)
        self.register_statement(node_name)

    # Analyze Vector operations
    # -------------------------
    # analyze_extractelement()
    # register_insertelement()

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

    # Analyze Aggregate operations
    # ----------------------------
    # analyze_extractvalue()
    # analyze_insertvalue()

    def analyze_extractvalue(self, tokens):
        self.rhs = self.extractvalue_analyzer.analyze_extractvalue(tokens)

        node_name = "extract value from {} at index ".format(self.rhs.get_value())
        for index in self.rhs.get_indices():
            node_name += "{}, ".format(index)

        self.register_statement(node_name[:-2])

    def analyze_insertvalue(self, tokens):
        self.rhs = self.insertvalue_analyzer.analyze_insertvalue(tokens)

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
    # analyze_load()
    # analyze_store()
    # analyze_getelementptr()

    def analyze_load(self, tokens):
        self.rhs = self.load_analyzer.analyze_load(tokens)
        self.register_statement(self.rhs.get_value())

    def analyze_store(self, tokens):
        self.rhs = self.store_analyzer.analyze_store(tokens)
        new_node = self.register_statement("{} = {}".format(self.rhs.get_register(), str(self.rhs.get_value())))

        self.opened_function_memory.assign_value_to_reg(self.rhs.get_register(), self.rhs.get_value())
        self.opened_function_memory.add_node_to_reg(self.rhs.get_register(), new_node)

    def analyze_getelementptr(self, tokens):
        self.rhs = self.getelementptr_analyzer.analyze_getelementptr(tokens)
        node_name = "getelementptr {}".format(self.rhs.get_value())
        for idx in self.rhs.get_indices():
            node_name += "[{}]".format(idx)
        self.register_statement(node_name)

    # Analyze Conversion operations
    # -----------------------------
    # analyze_trunc()
    # analyze_fpext()
    # analyze_sitofp()
    # analyze_bitcast()

    def analyze_trunc(self, tokens):
        self.rhs = self.trunc_analyzer.analyze_trunc(tokens)
        self.register_statement("trunc {} to {}".format(self.rhs.get_value(), self.rhs.get_final_type()))

    def analyze_fpext(self, tokens):
        self.rhs = self.fpext_analyzer.analyze_fpext(tokens)
        self.register_statement("fpext {} to {}".format(self.rhs.get_value(), self.rhs.get_final_type()))

    def analyze_sitofp(self, tokens):
        self.rhs = self.sitofp_analayzer.analyze_sitofp(tokens)
        self.register_statement("sitofp {} to {}".format(self.rhs.get_value(), self.rhs.get_final_type()))

    def analyze_bitcast(self, tokens):
        self.rhs = self.bitcast_analyzer.analyze_bitcast(tokens)
        self.register_statement("bitcast {} from {} to {}".format(self.rhs.get_value(),
                                                                  self.rhs.get_original_type(),
                                                                  self.rhs.get_final_type()))

    # Analyze Other operations
    # ------------------------
    # analyze_icmp()
    # analyze_phi()
    # analyze_call()
    # analyze_landingpad()

    def analyze_icmp(self, tokens):
        self.rhs = self.icmp_analyzer.analyze_icmp(tokens)
        self.register_statement("{} {} {}".format(self.rhs.get_value1(),
                                                  self.rhs.get_condition(),
                                                  self.rhs.get_value2()))

    def analyze_fcmp(self, tokens):
        self.rhs = self.fcmp_analyzer.analyze_fcmp(tokens)
        self.register_statement("{} {} {}".format(self.rhs.get_value1(),
                                                  self.rhs.get_condition(),
                                                  self.rhs.get_value2()))

    def analyze_phi(self, tokens):
        self.rhs = self.phi_analyzer.analyze_phi(tokens)
        node_name = ""
        for option in self.rhs.get_options():
            node_name += "{} if prev= {}".format(option.get_value(), option.get_label())
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

    def analyze_landingpad(self):
        prev_node = self.node_stack[self.opened_function][-1]

        new_node = self.add_node("landingpad")
        self.graphs[self.opened_function].add_edge(prev_node, new_node)

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
