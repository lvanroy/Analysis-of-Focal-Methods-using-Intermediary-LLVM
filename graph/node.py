class Node:
    def __init__(self, node_id, node_name):
        self.node_id = node_id
        self.node_name = node_name
        self.context = None
        self.arguments = list()
        self.final = False
        self.assertion = False
        self.start = False
        self.test_var = False

    def __str__(self):
        if self.final:
            return "{}[label=\"{}\", shape=doublecircle]".format(self.node_id, self.node_name)
        return "{}[label=\"{}\"]".format(self.node_id, self.node_name)

    def set_name(self, name):
        self.node_name = name

    def get_name(self):
        return self.node_name

    def get_id(self):
        return self.node_id

    def set_final(self):
        self.final = True

    def set_test(self):
        self.start = True

    def is_test(self):
        return self.start

    def set_assertion(self):
        self.assertion = True

    def is_assertion(self):
        return self.assertion

    def set_test_var(self):
        self.test_var = True

    def is_test_var(self):
        return self.test_var

    def add_argument(self, argument):
        self.arguments.append(argument)

    def get_arguments(self):
        return self.arguments

    def set_context(self, context):
        self.context = context

    def get_context(self):
        return self.context
