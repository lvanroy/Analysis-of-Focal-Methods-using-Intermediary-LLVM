class Memory:
    def __init__(self):
        self.memory = dict()

    def get_register_object(self, entry):
        if entry not in self.memory:
            self.memory[entry] = Register()
        return self.memory[entry]

    def __str__(self):
        output = ""
        for register in self.memory:
            output += "{}: {}\n".format(register, str(self.memory[register]))
        return output


class Register:
    def __init__(self):
        self.value = None

    def set_value(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)
