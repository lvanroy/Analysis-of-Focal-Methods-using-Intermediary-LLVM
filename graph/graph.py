from graph.node import Node
from graph.edge import Edge
from subprocess import call, DEVNULL
from os import path


class Graph:
    def __init__(self):
        self.nodes = list()
        self.edges = dict()
        self.needed_nodes = list()
        self.node_count = 0

    def add_node(self, node_name):
        self.nodes.append(Node("Q{}".format(self.node_count), node_name))
        self.node_count += 1
        return self.nodes[-1]

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

    def export_graph(self, filename):
        output = "digraph G {\n"

        for node in self.needed_nodes:
            output += "\t{};\n".format(node)

        for edge in self.edges:
            output += "\t{}\n".format(self.edges[edge])

        output += "}"

        if not path.exists("plots"):
            call(["mkdir", "plots"], stdout=DEVNULL)

        f = open("./plots/{}.dot".format(filename), "w")
        f.write(output)
        f.close()

        call(["dot", "-Tpng",  "./plots/{}.dot".format(filename), "-o",  "./plots/{}.png".format(filename)],
             stdout=DEVNULL)
