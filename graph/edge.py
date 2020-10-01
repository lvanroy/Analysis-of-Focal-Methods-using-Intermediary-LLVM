class Edge:
    def __init__(self, start_node, end_node):
        self.start_node = start_node
        self.end_node = end_node

    def __str__(self):
        return "{} -> {}".format(self.start_node.get_id(), self.end_node.get_id())
