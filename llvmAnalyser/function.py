from llvmAnalyser.llvmchecker import *
from llvmAnalyser.memory import Memory
from llvmAnalyser.types import get_type


# this handler will create all needed function objects from tokens
class FunctionHandler:
    def __init__(self):
        self.functions = dict()

    # return a function name if the tokens define a function
    # return None if not
    def identify_function(self, tokens):
        # skip the define keyword
        tokens.pop(0)

        # create the function object
        func = Function()

        # check linkage type
        if is_linkage_type(tokens[0]):
            func.set_linkage_type(tokens[0])
            tokens.pop(0)

        # check runtime preemption
        if is_runtime_preemptable(tokens[0]):
            func.set_runtime_preemption(tokens[0])
            tokens.pop(0)
        else:
            func.set_runtime_preemption("dso_preemptable")

        # check visibility style
        if is_visibility_style(tokens[0]):
            func.set_visibility_style(tokens[0])
            tokens.pop(0)

        # check DLL storage class
        if is_dll_storage_class(tokens[0]):
            func.set_dll_storage_class(tokens[0])
            tokens.pop(0)

        # check calling convention
        if is_calling_convention(tokens[0]):
            func.set_calling_convention(tokens[0])
            tokens.pop(0)
        else:
            func.set_calling_convention("ccc")

        # check return parameter attributes
        if tokens[0] == "align":
            tokens[0] = "{} {}".format(tokens[0], tokens[1])
            tokens.pop(1)
            tokens.pop(0)

        if is_parameter_attribute(tokens[0]):
            func.set_return_parameter_attribute(tokens[0])
            tokens.pop(0)

        # set return type
        ret_type, tokens = get_type(tokens)
        func.set_return_type(ret_type)

        # set function name
        new_tokens = tokens[0].split("(")
        tokens[0] = new_tokens[1]
        func.set_function_name(new_tokens[0])

        # read parameter data
        while True:
            # function without parameters
            if tokens[0] == ")":
                tokens.pop(0)
                break

            # read parameter type
            parameter = Parameter()
            parameter_type, tokens = get_type(tokens)
            parameter.set_parameter_type(parameter_type)

            # parameter with only parameter type
            if tokens[0] == ",":
                parameter.set_register("%{}".format(func.get_number_of_parameters()))
                func.add_parameter(parameter)
                tokens.pop(0)
                continue

            # read all parameter attributes
            if is_group_attribute(tokens[0]):
                parameter.set_group_parameter_attribute(tokens[0])
                tokens.pop(0)
            else:
                while "," not in tokens[0] and "%" not in tokens[0] and (")" not in tokens[0] or "(" in tokens[0]):
                    parameter.add_parameter_attribute(tokens[0])
                    tokens.pop(0)

            # read parameter name
            if "%" in tokens[0]:
                parameter.set_register(tokens[0].replace(",", "").replace(")", ""))

            # read final parameter attribute
            elif "," in tokens[0]:
                parameter.add_parameter_attribute(tokens[0].replace(",").replace(")", ""))
                parameter.set_register("%{}".format(func.get_number_of_parameters()))

            func.add_parameter(parameter)
            final = ')' in tokens[0]
            tokens.pop(0)

            # end of parameter list
            if final:
                break

        # check unnamed addr
        if is_unnamed_addr(tokens[0]):
            func.set_unnamed_address(tokens[0])
            tokens.pop(0)

        # check address space
        if is_address_space(tokens[0]):
            func.set_address_space(tokens[0])
            tokens.pop(0)

        # check function attributes
        if is_group_attribute(tokens[0]):
            func.set_group_function_attribute(tokens[0])
            tokens.pop(0)
        else:
            while is_function_attribute(tokens[0]):
                func.add_function_attribute(tokens[0])
                tokens.pop(0)

        # check section info
        if tokens[0] == "section":
            func.set_section(tokens[1])
            tokens.pop(1)
            tokens.pop(0)

        # check comdat info
        if tokens[0] == "comdat":
            if is_comdat(tokens[1]):
                func.set_comdat(tokens[1])
                tokens.pop(1)
            tokens.pop(0)

        # check alignment info
        if tokens[0] == "align":
            func.set_alignment(tokens[1])
            tokens.pop(1)
            tokens.pop(0)

        # check garbage collector name info
        if tokens[0] == "gc":
            func.set_garbage_collector_name(tokens[1])
            tokens.pop(1)
            tokens.pop(0)

        # check prefix info
        if tokens[0] == "prefix":
            func.set_prefix(tokens[1])
            tokens.pop(1)
            tokens.pop(0)

        # check prologue info
        if tokens[0] == "prologue":
            func.set_prologue(tokens[1])
            tokens.pop(1)
            tokens.pop(0)

        # check personality info
        if tokens[0] == "personality":
            personality = ""
            tokens.pop(0)
            while tokens[0] != "{" and not is_metadata(tokens[0]):
                personality = "{} {}".format(personality, tokens[0])
                tokens.pop(0)
            func.set_personality(personality)

        # check metadata info
        while is_metadata(tokens[0]):
            metadata = Metadata(tokens[0].replace("!", ""), tokens[1].replace("!", ""))
            func.add_metadata(metadata)
            tokens.pop(1)
            tokens.pop(0)

        finished = len(tokens) == 1
        if not finished:
            print("analysis did not finish for function: {}".format(func.function_name))
            print(tokens)

        self.functions[func.function_name] = func

        return func.function_name

    def get_function_memory(self, function_name):
        return self.functions[function_name].get_memory()

    def __str__(self):
        result = "The following {} functions were found within the llvm code:\n".format(len(self.functions))
        for key in self.functions:
            result += "{}\n".format(str(self.functions[key]))
        return result


# this class will define a function specified within llvm
class Function:
    def __init__(self):
        self.memory = Memory()

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

    def set_group_function_attribute(self, group):
        self.function_attributes = group

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

    def get_memory(self):
        return self.memory

    def __str__(self):
        result = "function with name {} and return type {}\n".format(self.function_name, self.return_type)
        if self.linkage_type is not None:
            result += "\tlinkage type = {}\n".format(self.linkage_type)
        if self.runtime_preemption is not None:
            result += "\truntime preemption = {}\n".format(self.runtime_preemption)
        if self.visibility_style is not None:
            result += "\tvisibility style = {}\n".format(self.visibility_style)
        if self.dll_storage_class is not None:
            result += "\tdll storage class = {}\n".format(self.dll_storage_class)
        if self.calling_convention is not None:
            result += "\tcalling convention = {}\n".format(self.calling_convention)
        if self.unnamed_address is not None:
            result += "\tunnamed address = {}\n".format(self.unnamed_address)
        if self.return_parameter_attribute is not None:
            result += "\treturn parameter attribute = {}\n".format(self.return_parameter_attribute)
        if len(self.parameters) != 0:
            result += "\t{} parameter(s):\n".format(len(self.parameters))
            for parameter in self.parameters:
                result += "\t\t{}\n".format(str(parameter))
        else:
            result += "\t0 parameters\n"
        if len(self.function_attributes) != 0:
            result += "\tfunction attributes = {}\n".format(self.function_attributes)
        if self.address_space is not None:
            result += "\taddress space = {}\n".format(self.address_space)
        if self.section is not None:
            result += "\tsection = {}\n".format(self.section)
        if self.alignment is not None:
            result += "\talignment = {}\n".format(self.alignment)
        if self.comdat is not None:
            result += "\tcomdat = {}\n".format(self.comdat)
        if self.garbage_collector_name is not None:
            result += "\tgarbage collector name = {}\n".format(self.garbage_collector_name)
        if self.prefix is not None:
            result += "\tprefix = {}\n".format(self.prefix)
        if self.prologue is not None:
            result += "\tprologue = {}\n".format(self.prologue)
        if self.personality is not None:
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

    def set_group_parameter_attribute(self, group):
        self.parameter_attributes = group

    def set_register(self, register):
        self.register = register

    def __str__(self):
        result = self.parameter_type
        if type(self.parameter_attributes) == list:
            for attr in self.parameter_attributes:
                result += " {}".format(attr)
        else:
            result += self.parameter_attributes
        result += " {}".format(self.register)
        return result


class Metadata:
    def __init__(self, identifier, value):
        self.identifier = identifier
        self.value = value

    def __str__(self):
        return "!{} !{}".format(self.identifier, self.value)
