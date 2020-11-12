"""
Class used to map all registers to the assigned values of that register
assigned value cna either be another register
"""


class Memory:
    def __init__(self):
        self.memory = dict()

    def assign_value_to_reg(self, reg, val):
        self.memory[reg] = Register(val)

    def __str__(self):
        output = ""
        for register in self.memory:
            output += "{}: {}\n".format(register, str(self.memory[register]))
        return output


class Register:
    def __init__(self, val):
        self.value = val

    def set_value(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)
