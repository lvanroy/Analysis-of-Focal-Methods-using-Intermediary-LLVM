from llvmAnalyser.llvmchecker import *


# this handler will create all needed function objects from tokens
class FunctionHandler:
    def __init__(self):
        self.functions = dict()

    # return a function object if the tokens define a function
    # return None if not
    def identify_function(self, tokens):
        if tokens[0] != "define":
            return None

        # specify the current token index
        i = 1

        # create the function object
        func = Function()

        # check linkage type
        if is_linkage_type(tokens[i]):
            func.set_linkage_type(tokens[i])
            i += 1

        # check runtime preemption
        if is_runtime_preemptable(tokens[i]):
            func.set_runtime_preemption(tokens[i])
            i += 1
        else:
            func.set_runtime_preemption("dso_preemptable")

        # check visibility style
        if is_visibility_style(tokens[i]):
            func.set_visibility_style(tokens[i])
            i += 1

        # check DLL storage class
        if is_dll_storage_class(tokens[i]):
            func.set_dll_storage_class(tokens[i])
            i += 1

        # check calling convention
        if is_calling_convention(tokens[i]):
            func.set_calling_convention(tokens[i])
            i += 1
        else:
            func.set_calling_convention("ccc")

        # check return parameter attributes
        if tokens[i] == "align":
            tokens[i] = "{} {}".format(tokens[i], tokens[i + 1])
            tokens.pop(i + 1)

        if is_parameter_attribute(tokens[i]):
            func.set_return_parameter_attribute(tokens[i])
            i += 1

        # set return type
        if tokens[i + 1] == "()":
            tokens[i] += " {}".format(tokens[i + 1])
            tokens.pop(i + 1)
        elif tokens[i + 1] == "()*":
            tokens[i] += " {}".format(tokens[i + 1])
            tokens.pop(i + 1)
        func.set_return_type(tokens[i])
        i += 1

        # set function name
        new_tokens = tokens[i].split("(")
        tokens[i] = new_tokens[0]
        tokens.insert(i + 1, new_tokens[1])
        func.set_function_name(tokens[i])
        i += 1

        # read parameter data
        while True:
            # function without parameters
            if tokens[i] == ")":
                i += 1
                break

            # read parameter type
            parameter = Parameter()
            parameter.set_parameter_type(tokens[i])

            # parameter with only parameter type
            if "," in tokens[i]:
                parameter.set_register("%{}".format(func.get_number_of_parameters()))
                func.add_parameter(parameter)
                continue

            i += 1

            # read all parameter attributes
            while "," not in tokens[i] and "%" not in tokens[i] and (")" in tokens[i] or ")" not in tokens[i]):
                parameter.add_parameter_attribute(tokens[i])
                i += 1

            # read parameter name
            if "%" in tokens[i]:
                parameter.set_register(tokens[i].replace(",", "").replace(")", ""))

            # read final parameter attribute
            elif "," in tokens[i]:
                parameter.add_parameter_attribute(tokens[i].replace(",").replace(")", ""))
                parameter.set_register("%{}".format(func.get_number_of_parameters()))

            func.add_parameter(parameter)
            i += 1

            # end of parameter list
            if ")" in tokens[i - 1]:
                break

        # check unnamed addr
        if is_unnamed_addr(tokens[i]):
            func.set_unnamed_address(tokens[i])
            i += 1

        # check address space
        if is_address_space(tokens[i]):
            func.set_address_space(tokens[i])
            i += 1

        # check function attributes
        while is_function_attribute(tokens[i]):
            func.add_function_attribute(tokens[i])
            i += 1

        # check section info
        if tokens[i] == "section":
            func.set_section(tokens[i + 1])
            i += 2

        # check comdat info
        if tokens[i] == "comdat":
            if is_comdat(tokens[i + 1]):
                func.set_comdat(tokens[i + 1])
                i += 2
            else:
                i += 1

        # check alignment info
        if tokens[i] == "align":
            func.set_alignment(tokens[i + 1])
            i += 2

        # check garbage collector name info
        if tokens[i] == "gc":
            func.set_garbage_collector_name(tokens[i + 1])
            i += 2

        # check prefix info
        if tokens[i] == "prefix":
            func.set_prefix(tokens[i + 1])
            i += 2

        # check prologue info
        if tokens[i] == "prologue":
            func.set_prologue(tokens[i + 1])
            i += 2

        # check personality info
        if tokens[i] == "personality":
            personality = ""
            i += 1
            while tokens[i] != "{\n" and not is_metadata(tokens[i]):
                personality = "{} {}".format(personality, tokens[i])
                i += 1
            func.set_personality(personality)

        # check metadata info
        while is_metadata(tokens[i]):
            metadata = Metadata(tokens[i].replace("!", ""), tokens[i + 1].replace("!", ""))
            func.add_metadata(metadata)
            i += 2

        finished = tokens[i] == "{\n"
        if not finished:
            print("all tokens analyzed: {}".format(finished))
            print(tokens)
            print(tokens[i])

        self.functions[func.function_name] = func

    def __str__(self):
        result = "The following {} functions were found within the llvm code:\n".format(len(self.functions))
        for key in self.functions:
            result += "{}\n".format(str(self.functions[key]))
        return result


# this class will define a function specified within llvm
class Function:
    def __init__(self):
        self.linkage_type = None
        self.runtime_preemption = None
        self.visibility_style = None
        self.dll_storage_class = None
        self.calling_convention = None
        self.unnamed_address = None
        self.return_type = None
        self.return_parameter_attribute = None
        self.function_name = None
        self.parameters = list()
        self.function_attributes = list()
        self.address_space = None
        self.section = None
        self.alignment = None
        self.comdat = None
        self.garbage_collector_name = None
        self.prefix = None
        self.prologue = None
        self.personality = None
        self.metadata = list()

    def set_linkage_type(self, linkage_type):
        self.linkage_type = linkage_type

    def set_runtime_preemption(self, runtime_preemption):
        self.runtime_preemption = runtime_preemption

    def set_visibility_style(self, visibility_style):
        self.visibility_style = visibility_style

    def set_dll_storage_class(self, dll_storage_class):
        self.dll_storage_class = dll_storage_class

    def set_calling_convention(self, calling_convention):
        self.calling_convention = calling_convention

    def set_unnamed_address(self, unnamed_address):
        self.unnamed_address = unnamed_address

    def set_return_type(self, return_type):
        self.return_type = return_type

    def set_return_parameter_attribute(self, return_parameter_attribute):
        self.return_parameter_attribute = return_parameter_attribute

    def set_function_name(self, function_name):
        self.function_name = function_name

    def add_parameter(self, parameter):
        self.parameters.append(parameter)

    def add_function_attribute(self, attribute):
        self.function_attributes.append(attribute)

    def set_address_space(self, address_space):
        self.address_space = address_space

    def set_section(self, section):
        self.section = section

    def set_alignment(self, alignment):
        self.alignment = alignment

    def set_comdat(self, comdat):
        self.comdat = comdat

    def set_garbage_collector_name(self, gc_name):
        self.garbage_collector_name = gc_name

    def set_prefix(self, prefix):
        self.prefix = prefix

    def set_prologue(self, prologue):
        self.prologue = prologue

    def set_personality(self, personality):
        self.personality = personality

    def add_metadata(self, metadata):
        self.metadata.append(metadata)

    def get_number_of_parameters(self):
        return len(self.parameters)

    def __str__(self):
        result = "function with name {} and return type {}\n".format(self.function_name, self.return_type)
        result += "\tlinkage type = {}\n".format(self.linkage_type)
        result += "\truntime preemption = {}\n".format(self.runtime_preemption)
        result += "\tvisibility style = {}\n".format(self.visibility_style)
        result += "\tdll storage class = {}\n".format(self.dll_storage_class)
        result += "\tcalling convention = {}\n".format(self.calling_convention)
        result += "\tunnamed address = {}\n".format(self.unnamed_address)
        result += "\treturn parameter attribute = {}\n".format(self.return_parameter_attribute)
        if len(self.parameters) != 0:
            result += "\t{} parameter(s):\n".format(len(self.parameters))
            for parameter in self.parameters:
                result += "\t\t{}\n".format(str(parameter))
        else:
            result += "\t0 parameters\n"
        result += "\tfunction attributes = {}\n".format(self.function_attributes)
        result += "\taddress space = {}\n".format(self.address_space)
        result += "\tsection = {}\n".format(self.section)
        result += "\talignment = {}\n".format(self.alignment)
        result += "\tcomdat = {}\n".format(self.comdat)
        result += "\tgarbage collector name = {}\n".format(self.garbage_collector_name)
        result += "\tprefix = {}\n".format(self.prefix)
        result += "\tprologue = {}\n".format(self.prologue)
        result += "\tpersonality = {}\n".format(self.personality)
        if len(self.metadata) != 0:
            result += "\t{} metadata items:\n".format(len(self.metadata))
            for metadata in self.metadata:
                result += "\t\t{}\n".format(str(metadata))
        else:
            result += "\t0 metadata items\n"
        return result


class Parameter:
    def __init__(self):
        self.parameter_type = None
        self.parameter_attributes = list()
        self.register = None

    def set_parameter_type(self, parameter_type):
        self.parameter_type = parameter_type

    def add_parameter_attribute(self, parameter_attribute):
        self.parameter_attributes.append(parameter_attribute)

    def set_register(self, register):
        self.register = register

    def __str__(self):
        result = self.parameter_type
        for attr in self.parameter_attributes:
            result += " {}".format(attr)
        result += " {}".format(self.register)
        return result


class Metadata:
    def __init__(self, identifier, value):
        self.identifier = identifier
        self.value = value

    def __str__(self):
        return "!{} !{}".format(self.identifier, self.value)
