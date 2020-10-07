from graph.graph import Graph
from llvmAnalyser.function import FunctionHandler
from llvmAnalyser.attributes import AttributeGroupHandler
from llvmAnalyser.call import CallAnalyzer
from llvmAnalyser.store import StoreAnalyzer
from llvmAnalyser.gtest import Gtest
from llvmAnalyser.types import get_array_type
from yaml import load

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader


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
        self.attribute_group_handler = AttributeGroupHandler()
        self.function_handler = FunctionHandler()
        self.call_analyzer = CallAnalyzer()
        self.store_analyzer = StoreAnalyzer()

        # keep track of the graph objects
        self.graphs = dict()
        self.top_graph = Graph()
        self.top_graph_nodes = dict()

        # keep track of the nodes that are added to the graphs, so that new nodes can be connected to the
        # previous ones in the chain
        self.node_stack = list()

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

        for line in lines:
            tokens = list(filter(None, line.replace("\t", "").replace("\n", "").split(" ")))

            if len(tokens) == 0:
                continue

            if tokens[0] == "define":
                self.analyze_define(tokens)
            elif tokens[0] == "attributes":
                self.analyze_attribute_group(tokens)
            elif tokens[0] == "ret":
                self.analyze_return()
            elif "=" in tokens and self.opened_function is not None:
                self.analyze_assignment(tokens)
            if "call" in tokens and self.opened_function is not None:
                self.analyze_call(tokens)
            if "store" in tokens and self.opened_function is not None:
                self.analyze_store(tokens)
            elif tokens[0] == "}":
                self.register_function_end()
            elif self.opened_function is not None:
                # print(tokens)
                self.node_stack.append(self.graphs[self.opened_function].add_node(tokens[0]))
                self.graphs[self.opened_function].add_edge(self.node_stack[-2], self.node_stack[-1])

            self.assignee = None

        if self.config["debug"]:
            print(self.function_handler)
        # print(self.attribute_group_handler)

        if self.config["graph"]:
            # for graph in self.graphs:
            # self.graphs[graph].export_graph(graph)
            self.top_graph.export_graph("top_level_graph")

    def analyze_define(self, tokens):
        self.opened_function = self.function_handler.identify_function(tokens)
        self.opened_function_memory = self.function_handler.get_function_memory(self.opened_function)
        self.graphs[self.opened_function] = Graph()
        self.node_stack.append(self.graphs[self.opened_function].add_node(self.opened_function))
        if self.opened_function not in self.top_graph_nodes:
            top_graph_node = self.top_graph.add_node(self.opened_function)
            self.top_graph_nodes[self.opened_function] = top_graph_node
        if self.function_handler.is_startup_func(self.opened_function):
            self.top_graph_nodes[self.opened_function].set_start()

    def analyze_attribute_group(self, tokens):
        self.attribute_group_handler.identify_attribute_groups(tokens)

    def analyze_return(self):
        self.node_stack.append(self.graphs[self.opened_function].add_final_node("ret"))
        self.graphs[self.opened_function].add_edge(self.node_stack[-2], self.node_stack[-1])

    def analyze_call(self, tokens):
        call = self.call_analyzer.analyze_call(tokens)
        function_name = call.function_name
        function_call = "call {}".format(function_name)

        self.node_stack.append(self.graphs[self.opened_function].add_node(function_call))
        self.graphs[self.opened_function].add_edge(self.node_stack[-2], self.node_stack[-1])
        if function_name in self.top_graph_nodes:
            final_node = self.top_graph_nodes[function_name]
        else:
            final_node = self.top_graph.add_node(function_name)
            self.top_graph_nodes[function_name] = final_node
        first_node = self.top_graph_nodes[self.opened_function]
        self.top_graph.add_edge(first_node, final_node)

        if self.assignee is not None:
            self.assignee.set_value(call)

    def analyze_store(self, tokens):
        self.store_analyzer.analyzer_store(tokens, self.opened_function_memory)

    # def analyze_alloca(self, tokens):
    # self.alloca_analyzer.analyze_alloca_instruction(tokens)

    def analyze_assignment(self, tokens):
        self.assignee = self.opened_function_memory.get_register_object(tokens[0])

    def register_function_end(self):
        # print(self.opened_function)
        # print(self.opened_function_memory)
        self.opened_function = None
        self.opened_function_memory = None
        self.node_stack = list()
