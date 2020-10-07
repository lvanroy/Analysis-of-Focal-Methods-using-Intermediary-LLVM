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

    def add_node(self, node_name):
        self.nodes[node_name] = Node("Q{}".format(self.node_count), node_name)
        self.node_count += 1
        return self.nodes[node_name]

    def add_final_node(self, node_name):
        node = self.add_node(node_name)
        node.set_final()
        return node

    def add_edge(self, start_node, end_node):
        key = frozenset([start_node, end_node])

        if key not in self.edges:
            if start_node not in self.needed_nodes:
                self.needed_nodes.append(start_node)
            if end_node not in self.needed_nodes:
                self.needed_nodes.append(end_node)
            self.edges[key] = Edge(start_node, end_node)
        return self.edges[key]

    def make_node_start_node(self, node_name):
        self.nodes[node_name].set_start()

    def export_graph(self, filename):

        changes_occured = True
        added_nodes = list()

        for node in self.needed_nodes:
            if node.is_start():
                added_nodes.append(node)

        while changes_occured:
            changes_occured = False
            for edge in self.edges:
                if self.edges[edge].start_node in added_nodes and self.edges[edge].end_node not in added_nodes:
                    changes_occured = True
                    added_nodes.append(self.edges[edge].end_node)

        output = "digraph G {\n"

        for node in added_nodes:
            if node.is_start():
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
