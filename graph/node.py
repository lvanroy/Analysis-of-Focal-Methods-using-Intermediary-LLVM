class Node:
    def __init__(self, node_id, node_name):
        self.node_id = node_id
        self.node_name = node_name
        self.final = False
        self.start = False

    def __str__(self):
        if self.final:
            return "{}[label=\"{}\", shape=doublecircle]".format(self.node_id, self.node_name)
        return "{}[label=\"{}\"]".format(self.node_id, self.node_name)

    def get_id(self):
        return self.node_id

    def set_final(self):
        self.final = True

    def set_start(self):
        self.start = True

    def is_start(self):
        return self.start
