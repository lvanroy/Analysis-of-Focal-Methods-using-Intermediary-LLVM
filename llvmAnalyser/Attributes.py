from llvmAnalyser.llvmchecker import is_attribute


class AttributeGroupHandler:
    def __init__(self):
        self.groups = dict()

    def identify_attribute_groups(self, tokens):
        group = AttributeGroup()
        group.set_id(tokens[1])

        i = 4
        while tokens[i] != "}\n":
            if is_attribute(tokens[i]):
                group.add_attribute(tokens[i])
            i += 1

        self.groups[tokens[1]] = group

    def get_attributes_for_id(self, group_id):
        return self.groups[group_id].get_attributes()

    def __str__(self):
        result = ""
        for group in self.groups:
            result = "{}\n{}".format(result, str(self.groups[group]))
        return result


class AttributeGroup:
    def __init__(self):
        self.group_id = None
        self.attributes = list()

    def set_id(self, group_id):
        self.group_id = group_id

    def add_attribute(self, attr):
        self.attributes.append(attr)

    def get_attributes(self):
        return self.attributes

    def __str__(self):
        result = "{}: ".format(self.group_id)
        for attr in self.attributes:
            result += "{}, ".format(attr)
        return result
