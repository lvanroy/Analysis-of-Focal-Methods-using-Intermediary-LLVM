"""
Class used to map all registers to the assigned values of that register
assigned value cna either be another register
"""


class Memory:
    def __init__(self):
        self.memory = dict()

    def assign_value_to_reg(self, reg, val):
        self.memory[reg] = Register(val)

    def add_node_to_reg(self, reg, node):
        self.memory[reg].set_node(node)

    def is_reg_in_mem(self, reg):
        return reg in self.memory

    def get_node(self, reg):
        if reg in self.memory:
            return self.memory[reg].get_node()
        else:
            return None

    def get_val(self, reg):
        return self.memory[reg].value

    def __str__(self):
        output = ""
        for register in self.memory:
            output += "{}: {}\n".format(register, str(self.memory[register]))
        return output


class Register:
    def __init__(self, val):
        self.value = val
        self.node = None

    def set_value(self, value):
        self.value = value

    def set_node(self, node):
        self.node = node

    def get_node(self):
        return self.node

    def __str__(self):
        return "{}\n{}".format(str(self.value), self.node)
