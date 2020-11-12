from llvmAnalyser.types import get_type


class InsertvalueAnalyzer:
    def __init__(self):
        pass

    @staticmethod
    def analyze_insertvalue(tokens):
        insertvalue_instruction = Insertvalue()

        # pop the assignment segment
        while tokens[0] != "insertvalue":
            tokens.pop(0)

        # pop the insertvalue instruction
        tokens.pop(0)

        # get the object type
        object_type, tokens = get_type(tokens)
        insertvalue_instruction.set_object_type(object_type)

        # get the original object
        insertvalue_instruction.set_original(tokens[0].replace(",", ""))
        tokens.pop(0)

        # get the type and value that is to be inserted
        insert_type, tokens = get_type(tokens)
        insertvalue_instruction.set_insert_type(insert_type)
        insertvalue_instruction.set_insert_value(tokens[0].replace(",", ""))
        tokens.pop(0)

        while len(tokens) != 0:
            insertvalue_instruction.add_index(tokens[0].replace(",", ""))
            tokens.pop(0)

        return insertvalue_instruction


class Insertvalue:
    def __init__(self):
        self.object_type = None
        self.original = None
        self.insert_type = None
        self.insert_value = None
        self.indices = list()

    def set_object_type(self, object_type):
        self.object_type = object_type

    def set_original(self, original):
        self.original = original

    def set_insert_type(self, insert_type):
        self.insert_type = insert_type

    def set_insert_value(self, insert_value):
        self.insert_value = insert_value

    def add_index(self, index):
        self.indices.append(index)

    def get_object_type(self):
        return self.object_type

    def get_original(self):
        return self.original

    def get_insert_type(self):
        return self.insert_type

    def get_insert_value(self):
        return self.insert_value

    def get_indices(self):
        return self.indices

    def get_used_variables(self):
        if self.original == "undef":
            return list()
        return [self.original]
