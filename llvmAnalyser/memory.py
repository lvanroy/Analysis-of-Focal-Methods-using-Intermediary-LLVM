"""
Class used to map all registers to the assigned values of that register
assigned value cna either be another register
"""


class Memory:
    def __init__(self):
        self.memory = dict()
        self.addr_mod = dict()

    def assign_value_to_reg(self, reg, val):
        self.memory[reg] = Register(val)

    def assign_value_to_addr(self, addr, val):
        self.addr_mod[addr] = Register(val)

    def add_node_to_reg(self, reg, node):
        self.memory[reg].set_node(node)

    def add_node_to_addr(self, addr, node):
        self.addr_mod[addr].set_node(node)

    def is_reg_in_mem(self, reg):
        return reg in self.memory

    def get_node(self, reg):
        if reg in self.memory:
            return self.memory[reg].get_node()
        else:
            return None

    def get_val(self, reg):
        if reg in self.memory:
            return self.memory[reg].value
        else:
            return None

    def get_addr_val(self, reg):
        if reg in self.addr_mod:
            return self.addr_mod[reg].value
        else:
            return None

    def get_lvals(self, rval):
        ret = list()
        for instance in self.memory:
            temp_val = self.memory[instance].value

            if rval in temp_val.get_used_variables():
                ret.append(instance)

        for instance in self.addr_mod:
            temp_val = self.addr_mod[instance].value

            if temp_val == rval:
                ret.append(instance)

        return ret

    def __str__(self):
        output = "registers:\n"
        for register in self.memory:
            output += "{}: {}\n".format(register, str(self.memory[register]))

        output += "\naddress mod:\n"
        for register in self.addr_mod:
            output += "{}: {}\n".format(register, str(self.addr_mod[register]))
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
        return "{}".format(str(self.value))
