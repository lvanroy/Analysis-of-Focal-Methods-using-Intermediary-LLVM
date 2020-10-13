from graph.node import Node
from graph.edge import Edge
from subprocess import call, DEVNULL
from os import path


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

    def register_start_of_block(self, block_name):
        self.block_map[block_name] = self.nodes[block_name]

    def get_start_of_block(self, block_name):
        if block_name in self.block_map:
            return self.block_map[block_name]
        return None

    def set_test_func(self):
        self.test_func = True

    def is_test_func(self):
        return self.test_func

    def add_node(self, node_name):
        self.nodes[node_name] = Node("Q{}".format(self.node_count), node_name.translate(self.trans))
        self.node_count += 1
        return self.nodes[node_name]

    def add_final_node(self, node_name):
        node = self.add_node(node_name)
        node.set_final()
        return node

    def add_edge(self, start_node, end_node, label=""):
        key = frozenset([start_node, end_node, label])

        if key not in self.edges:
            if start_node not in self.needed_nodes:
                self.needed_nodes.appenself.neededd(start_node)
            if end_node not in _nodes:
                self.needed_nodes.append(end_node)
            self.edges[key] = Edge(start_node, end_node, label)
        return self.edges[key]

    def make_node_start_node(self, node_name):
        self.nodes[node_name.translate(self.trans)].set_start()

    def export_graph(self, filename):
        changes_occured = True
        added_nodes = list()

        for node in self.needed_nodes:
            if node.is_test():
                added_nodes.append(node)

        while changes_occured:
            changes_occured = False
            for edge in self.edges:
                if self.edges[edge].start_node in added_nodes and self.edges[edge].end_node not in added_nodes:
                    changes_occured = True
                    added_nodes.append(self.edges[edge].end_node)

        output = "digraph G {\n"

        for node in added_nodes:
            if node.is_test():
                output += "\t{}, fillcolor=green, style=filled];\n".format(str(node)[:-1])
            else:
                output += "\t{};\n".format(node)

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
