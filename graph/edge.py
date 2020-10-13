class Edge:
    def __init__(self, start_node, end_node, label):
        self.start_node = start_node
        self.end_node = end_node
        self.label = label

    def __str__(self):
        return "{} -> {} [label = \"{}\"]".format(self.start_node.get_id(), self.end_node.get_id(), self.label)
