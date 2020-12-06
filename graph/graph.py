from graph.node import Node
from graph.edge import Edge
from subprocess import call, DEVNULL
from os import path
import re


class Graph:
    def __init__(self):
        self.nodes = dict()
        self.edges = dict()
        self.needed_nodes = list()
        self.node_count = 0
        self.trans = str.maketrans({"\"": "\\\""})
        self.test_func = False

        # this dict will be used to map block names to the corresponding start nodes
        self.block_map = dict()

        # keep track of the assertion nodes, these will be used to start the focal method analysis from
        self.assertions = list()

        self.func = re.compile(r'^.*(= )?call .*$')

    def register_start_of_block(self, block_name):
        for node in self.nodes.values():
            if node.get_name() == block_name:
                self.block_map[block_name] = node

    def get_start_of_block(self, block_name):
        if block_name in self.block_map:
            return self.block_map[block_name]
        return None

    def set_test_func(self):
        self.test_func = True

    def is_test_func(self):
        return self.test_func

    def add_node(self, node_name):
        self.nodes[self.node_count] = Node("Q{}".format(self.node_count), node_name.translate(self.trans))
        self.node_count += 1
        return self.nodes[self.node_count-1]

    def add_final_node(self, node_name):
        node = self.add_node(node_name)
        node.set_final()
        return node

    def add_edge(self, start_node, end_node, label=""):
        key = frozenset([start_node, end_node, label])

        if key not in self.edges:
            if start_node not in self.needed_nodes:
                self.needed_nodes.append(start_node)
            if end_node not in self.needed_nodes:
                self.needed_nodes.append(end_node)
            self.edges[key] = Edge(start_node, end_node, label)
            start_node.add_out(end_node)
            end_node.add_inc(start_node)
        return self.edges[key]

    def make_node_start_node(self, node_name):
        for node in self.nodes.values():
            if node.get_name() == node_name:
                node.set_start()

    def add_assertion(self, node):
        self.assertions.append(node)

    # this function is used to check for assert helpers, which are functions that link test code to the specific assert
    # functions
    def check_for_assert_helpers(self):
        changes_occurred = True
        assert_helpers = list()

        while changes_occurred:
            changes_occurred = False
            for node in self.nodes.values():
                if not node.is_assertion():
                    continue
                if node.get_name() not in assert_helpers:
                    assert_helpers.append(node.get_name())
                for edge in self.edges.values():
                    if edge.end_node == node and not edge.start_node.is_assertion() and not edge.start_node.is_test():
                        edge.start_node.set_assertion()
                        changes_occurred = True

        return assert_helpers

    # this function is used to check for variables under test
    def check_for_used_assertion(self, assert_helpers):
        assertions = list()
        for node in self.nodes.values():
            if not self.func.match(node.get_name()):
                continue
            function = node.get_name().split("call ")[1]
            if function in assert_helpers:
                node.set_assertion()
                assertions.append(node)

        return assertions

    def export_graph(self, filename):
        changes_occurred = True
        added_nodes = list()

        for node in self.needed_nodes:
            if node.is_test():
                added_nodes.append(node)

        while changes_occurred:
            changes_occurred = False
            for edge in self.edges:
                if self.edges[edge].start_node in added_nodes and self.edges[edge].end_node not in added_nodes:
                    changes_occurred = True
                    added_nodes.append(self.edges[edge].end_node)

        output = "digraph G {\n"

        for node in added_nodes:
            if node.is_test():
                output += "\t{}, fontcolor=green];\n".format(str(node)[:-1])
            elif node.is_assertion():
                output += "\t{}, fontcolor=red];\n".format(str(node)[:-1])
            elif node.is_test_var():
                output += "\t{}, fontcolor=blue];\n".format(str(node)[:-1])
            else:
                output += "\t{};\n".format(node)

            if self.func.match(node.get_name()):
                arguments = node.get_arguments()
                if len(arguments) != 0:
                    argument_header = self.add_node("arguments")
                    output += "\t{};\n".format(argument_header)
                    output += "\t{} -> {};\n".format(node.get_id(), argument_header.get_id())
                    for argument in arguments:
                        output += "\t{};\n".format(argument)
                        output += "\t{} -> {};\n".format(argument_header.get_id(), argument.get_id())

        for edge in self.edges:
            if self.edges[edge].start_node in added_nodes and self.edges[edge].end_node in added_nodes:
                output += "\t{}\n".format(self.edges[edge])

        output += "}"

        if not path.exists("plots"):
            call(["mkdir", "plots"], stdout=DEVNULL)

        f = open("./plots/{}.dot".format(filename), "w")
        f.write(output)
        f.close()

        call(["dot", "-Tpng", "./plots/{}.dot".format(filename), "-o", "./plots/{}.png".format(filename)],
             stdout=DEVNULL)
