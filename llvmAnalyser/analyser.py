from graph.graph import Graph
from yaml import load
import re

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

from llvmAnalyser.function import FunctionHandler
from llvmAnalyser.attributes import AttributeGroupHandler
from llvmAnalyser.gtest import Gtest

from llvmAnalyser.terminator.br import BrAnalyzer
from llvmAnalyser.terminator.switch import SwitchAnalyzer
from llvmAnalyser.terminator.invoke import InvokeAnalyzer
from llvmAnalyser.terminator.resume import ResumeAnalyzer

from llvmAnalyser.binary.binaryOp import BinaryOpAnalyzer

from llvmAnalyser.aggregate.insertvalue import InsertvalueAnalyzer
from llvmAnalyser.aggregate.extractvalue import ExtractvalueAnalyzer

from llvmAnalyser.memoryAccess.store import StoreAnalyzer
from llvmAnalyser.memoryAccess.load import LoadAnalyzer
from llvmAnalyser.memoryAccess.getelementptr import GetelementptrAnalyzer

from llvmAnalyser.conversion.bitcast import BitcastAnalyzer

from llvmAnalyser.other.call import CallAnalyzer

block_start_format = re.compile(r'[0-9]*:')


# test_identifier must be a class that contains a identify test function member
# this function should return a boolean indicating whether or not the function is a test function

class LLVMAnalyser:
    def __init__(self):
        # load the config
        self.config = load(open('config.yml').read(), Loader=Loader)

        # register a test analyzer to determine which function signature should be used to discover which functions
        # are tests
        self.test_identifier = None
        if self.config["c++"]["test_framework"] == "gtest":
            self.test_identifier = Gtest

        # make handlers for the specific llvm statements
        self.function_handler = FunctionHandler()
        self.attribute_group_handler = AttributeGroupHandler()

        self.br_analyzer = BrAnalyzer()
        self.switch_analyzer = SwitchAnalyzer()
        self.invoke_analyzer = InvokeAnalyzer()
        self.resume_analyzer = ResumeAnalyzer()

        self.binary_op_analyzer = BinaryOpAnalyzer()

        self.insertvalue_analyzer = InsertvalueAnalyzer()
        self.extractvalue_analyzer = ExtractvalueAnalyzer()

        self.store_analyzer = StoreAnalyzer()
        self.load_analyzer = LoadAnalyzer()
        self.getelementptr_analyzer = GetelementptrAnalyzer()

        self.bitcast_analyzer = BitcastAnalyzer()

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
                self.analyze_return()

            # register br statement
            elif "br" in tokens and self.opened_function is not None:
                self.analyze_br(tokens)

            # register switch statement
            elif "switch" in tokens and self.opened_function is not None:
                for _ in range(3):
                    tokens += list(filter(None, lines[1].replace("\t", "").replace("\n", "").split(" ")))
                    lines.pop(1)
                self.analyze_switch(tokens)

            # register invoke statement
            elif "invoke" in tokens and self.opened_function is not None:
                tokens += list(filter(None, lines[1].replace("\t", "").replace("\n", "").split(" ")))
                lines.pop(1)
                self.analyze_invoke(tokens)

            # register resume statement
            elif "resume" in tokens and self.opened_function is not None:
                self.analyze_resume(tokens)

            # register unreachable statement
            elif "unreachable" in tokens and self.opened_function is not None:
                self.analyze_unreachable()

            # Binary operations
            # -----------------
            # Binary operations are used for most computations in a program. They require two operands of the same type
            # and it results in a single value on which the operation is applied.
            # The binary operators are split into two main categories,
            #   operations on integer or vector of integer values, simply referred to as binary operations
            #   operations on floating-point or vector of floating-point values, referred to as floating-point binary
            #       operations

            # register binary integer operation
            elif len(tokens) > 2 and tokens[2] in ["add"] and self.opened_function is not None:
                self.analyze_binary_op(tokens)

            # Vector operations
            # -----------------
            # Vector operations cover element-access and vector-specific operations needed to process vectors
            # effectively.
            # The vector instructions are:
            #   'extractelement', 'insertelement', 'shufflevector'

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

            # register bitcast statement
            elif "bitcast" in tokens and self.opened_function is not None:
                self.analyze_bitcast(tokens)

            # other operations
            # ----------------
            # The other instructions are specified as other, due to lack of better classification. These are general
            # cross operation set operations. The llvm instruction set contains the following operations of type other:
            #   'icmp', 'fcmp', 'phi', 'select', 'freeze', 'call', 'va_arg', 'landingpad', 'catchpad', 'cleanuppad'

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
                    self.node_stack[self.opened_function][-1].set_name(new_name)
                self.assignee = None

            lines.pop(0)

        if self.config["graph"]:
            self.top_graph.export_graph("top_level_graph")
            for graph in self.graphs:
                if self.graphs[graph].is_test_func():
                    self.graphs[graph].export_graph(graph)

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

    def analyze_attribute_group(self, tokens):
        self.attribute_group_handler.identify_attribute_groups(tokens)

    # Analyze Terminator instructions
    # -------------------------------
    # analyze_return()
    # analyze_br()
    # analyze_switch()
    # analyze_invoke()
    # analyze_resume()
    # analyze_unreachable()

    def analyze_return(self):
        prev_node = self.node_stack[self.opened_function][-1]
        new_node = self.add_node("ret")
        new_node.set_final()
        self.graphs[self.opened_function].add_edge(prev_node, new_node)

    def analyze_br(self, tokens):
        br = self.br_analyzer.analyze_br(tokens)
        prev_node = self.node_stack[self.opened_function][-1]

        new_node = self.add_node("br")
        self.graphs[self.opened_function].add_edge(prev_node, new_node)

        block_name = "{}:{}".format(self.opened_function, br.get_label1())
        first_branch = self.get_first_node_of_block(block_name)
        self.graphs[self.opened_function].add_edge(new_node, first_branch)

        if br.get_label2() is not None:
            block_name = "{}:{}".format(self.opened_function, br.get_label2())
            second_branch = self.get_first_node_of_block(block_name)
            self.graphs[self.opened_function].add_edge(new_node, second_branch)

    def analyze_switch(self, tokens):
        switch = self.switch_analyzer.analyze_switch(tokens)
        prev_node = self.node_stack[self.opened_function][-1]

        new_node = self.add_node("switch")
        self.graphs[self.opened_function].add_edge(prev_node, new_node)

        block_name = "{}:{}".format(self.opened_function, switch.get_default())
        def_node = self.get_first_node_of_block(block_name)
        self.graphs[self.opened_function].add_edge(new_node, def_node, "default")

        for branch in switch.get_branches():
            block_name = "{}:{}".format(self.opened_function, branch.get_destination())
            branch_node = self.get_first_node_of_block(block_name)
            self.graphs[self.opened_function].add_edge(new_node, branch_node, "= {}".format(branch.get_condition()))

    def analyze_invoke(self, tokens):
        invoke = self.invoke_analyzer.analyze_invoke(tokens)
        prev_node = self.node_stack[self.opened_function][-1]

        new_node = self.add_node(invoke.get_func())
        self.graphs[self.opened_function].add_edge(prev_node, new_node)

        block_name = "{}:{}".format(self.opened_function, invoke.get_normal())
        normal_node = self.get_first_node_of_block(block_name)
        self.graphs[self.opened_function].add_edge(new_node, normal_node, "normal")

        block_name = "{}:{}".format(self.opened_function, invoke.get_exception())
        exception_node = self.get_first_node_of_block(block_name)
        self.graphs[self.opened_function].add_edge(new_node, exception_node, "exception")

    def analyze_resume(self, tokens):
        prev_node = self.node_stack[self.opened_function][-1]
        resume = self.resume_analyzer.analyze_resume(tokens)

        new_node = self.add_node("resume {} {}".format(resume.get_type(), resume.get_type()))
        self.graphs[self.opened_function].add_edge(prev_node, new_node)

    def analyze_unreachable(self):
        prev_node = self.node_stack[self.opened_function][-1]

        new_node = self.add_node("unreachable")
        self.graphs[self.opened_function].add_edge(prev_node, new_node)

    # Analyze Binary operations
    # -------------------------
    # analyze_binary_op()

    def analyze_binary_op(self, tokens):
        prev_node = self.node_stack[self.opened_function][-1]

        op = self.binary_op_analyzer.analyze_binary_op(tokens)
        new_node = self.add_node("{} {} {}".format(op.get_value1(), op.get_op(), op.get_value2()))
        self.graphs[self.opened_function].add_edge(prev_node, new_node)

    # Analyze Aggregate operations
    # ----------------------------
    # analyze_extractvalue()
    # analyze_insertvalue()

    def analyze_extractvalue(self, tokens):
        extractvalue = self.extractvalue_analyzer.analyze_extractvalue(tokens)
        prev_node = self.node_stack[self.opened_function][-1]

        node_name = "extract value from {} at index ".format(extractvalue.get_value())

        for index in extractvalue.get_indices():
            node_name += "{}, ".format(index)
        new_node = self.add_node(node_name[:-2])
        self.graphs[self.opened_function].add_edge(prev_node, new_node)

    def analyze_insertvalue(self, tokens):
        insertvalue = self.insertvalue_analyzer.analyze_insertvalue(tokens)
        prev_node = self.node_stack[self.opened_function][-1]

        if insertvalue.get_original() != "undef":
            node_name = "insert {} in {} at index ".format(insertvalue.get_insert_value(), insertvalue.get_original())
        else:
            node_name = "insert {} in new object of type {} at index ".format(insertvalue.get_insert_value(),
                                                                              insertvalue.get_object_type())
        for index in insertvalue.get_indices():
            node_name += "{}, ".format(index)
        new_node = self.add_node(node_name[:-2])
        self.graphs[self.opened_function].add_edge(prev_node, new_node)

    # Analyze Memory Access and Addressing operations
    # -----------------------------------------------
    # analyze_load()
    # analyze_store()
    # analyze_getelementptr()

    def analyze_load(self, tokens):
        load_instruction = self.load_analyzer.analyze_load(tokens)
        prev_node = self.node_stack[self.opened_function][-1]

        new_node = self.add_node(load_instruction.get_value())
        self.graphs[self.opened_function].add_edge(prev_node, new_node)

    def analyze_store(self, tokens):
        store = self.store_analyzer.analyze_store(tokens)
        prev_node = self.node_stack[self.opened_function][-1]

        new_node = self.add_node("{} = {}".format(store.get_register(), store.get_value()))
        self.graphs[self.opened_function].add_edge(prev_node, new_node)

    def analyze_getelementptr(self, tokens):
        getelementptr_instruction = self.getelementptr_analyzer.analyze_getelementptr(tokens)
        prev_node = self.node_stack[self.opened_function][-1]

        node_name = "getelementptr {}".format(getelementptr_instruction.get_value())
        for idx in getelementptr_instruction.get_indices():
            node_name += "[{}]".format(idx)
        new_node = self.add_node(node_name)
        self.graphs[self.opened_function].add_edge(prev_node, new_node)

    def analyze_call(self, tokens):
        call = self.call_analyzer.analyze_call(tokens)
        function_name = call.function_name
        function_call = "call {}".format(function_name)

        prev_node = self.node_stack[self.opened_function][-1]
        new_node = self.add_node(function_call)
        self.graphs[self.opened_function].add_edge(prev_node, new_node)
        if function_name in self.top_graph_nodes:
            final_node = self.top_graph_nodes[function_name]
        else:
            final_node = self.top_graph.add_node(function_name)
            self.top_graph_nodes[function_name] = final_node
        first_node = self.top_graph_nodes[self.opened_function]
        self.top_graph.add_edge(first_node, final_node)

    def analyze_bitcast(self, tokens):
        bitcast = self.bitcast_analyzer.analyze_bitcast(tokens)
        prev_node = self.node_stack[self.opened_function][-1]

        new_node = self.add_node("bitcast {} from {} to {}".format(bitcast.get_value(),
                                                                   bitcast.get_original_type(),
                                                                   bitcast.get_final_type()))
        self.graphs[self.opened_function].add_edge(prev_node, new_node)

    def analyze_landingpad(self):
        prev_node = self.node_stack[self.opened_function][-1]

        new_node = self.add_node("landingpad")
        self.graphs[self.opened_function].add_edge(prev_node, new_node)

    def analyze_assignment(self, tokens):
        self.assignee = tokens[0]

    def register_function_end(self):
        self.opened_function_memory = None
        self.opened_function = None

    def get_first_node_of_block(self, block_name):
        start = self.graphs[self.opened_function].get_start_of_block(block_name.split(":")[1])
        if start is not None:
            return start
        else:
            self.node_stack[block_name] = list()
            new_node = self.add_node(block_name.split(":")[1])
            self.graphs[self.opened_function].register_start_of_block(block_name.split(":")[1])
            return new_node

    def add_node(self, node_name):
        new_node = self.graphs[self.opened_function].add_node(node_name)
        self.node_stack[self.opened_function].append(new_node)
        return new_node
