from llvmAnalyser.llvmChecker import *
from llvmAnalyser.memory import Memory
from llvmAnalyser.types import get_type
from llvmAnalyser.values import get_value
from copy import copy
# LLVM function definitions consist of the “define” keyword, an optional linkage type,
# an optional runtime preemption specifier, an optional visibility style, an optional DLL storage class,
# an optional calling convention, an optional unnamed_addr attribute, a return type,
# an optional parameter attribute for the return type, a function name,
# a (possibly empty) argument list (each with optional parameter attributes), optional function attributes,
# an optional address space, an optional section, an optional alignment,
# an optional comdat, an optional garbage collector name, an optional prefix, an optional prologue,
# an optional personality, an optional list of attached metadata, an opening curly brace, a list of basic blocks,
# and a closing curly brace.

# define [linkage] [PreemptionSpecifier] [visibility] [DLLStorageClass]
#        [cconv] [ret attrs]
#        <ResultType> @<FunctionName> ([argument list])
#        [(unnamed_addr|local_unnamed_addr)] [AddrSpace] [fn Attrs]
#        [section "name"] [comdat [($name)]] [align N] [gc] [prefix Constant]
#        [prologue Constant] [personality Constant] (!name !N)* { ... }


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
            if func.get_calling_convention() == "cc":
                func.set_calling_convention("cc {}".format(tokens.pop(0)))
        else:
            func.set_calling_convention("ccc")

        # check return parameter attributes
        if is_parameter_attribute(tokens[0]):
            open_brackets = tokens[0].count("(") - tokens[0].count(")")
            attribute = tokens.pop(0)
            while open_brackets != 0:
                open_brackets += tokens[0].count("(") - tokens[0].count(")")
                attribute += tokens.pop(0)
            if attribute == "align":
                attribute += " {}".format(tokens.pop(0))
            func.set_return_parameter_attribute(attribute)

        # set return type
        ret_type, tokens = get_type(tokens)
        func.set_return_type(ret_type)

        # set function name
        new_tokens = tokens[0].split("(", 1)
        tokens[0] = new_tokens[1]
        func.set_function_name(new_tokens[0])

        final_bracket_token = get_nr_of_tokens_past_last_bracket(tokens)

        if tokens[0] == ")":
            tokens.pop(0)

        # read parameter data
        while len(tokens) >= final_bracket_token:
            # function without parameters
            if tokens[0] == ")":
                tokens.pop(0)
                break

            parameter = Parameter()

            if "..." in tokens[0]:
                parameter.set_register("...")
                tokens.pop(0)
                func.add_parameter(parameter)
                break

            old_tokens = copy(tokens)

            # read parameter type
            parameter_type, tokens = get_type(tokens)
            parameter.set_parameter_type(parameter_type)

            # read all parameter attributes
            if is_group_attribute(tokens[0]):
                parameter.set_group_parameter_attribute(tokens[0])
                tokens.pop(0)
            else:
                while is_parameter_attribute(tokens[0]):
                    open_brackets = tokens[0].count("(") - tokens[0].count(")")
                    attribute = tokens.pop(0)
                    while True:
                        if open_brackets <= 0:
                            break
                        for j in range(len(tokens[0])):
                            char = tokens[0][j]
                            if char == "(":
                                open_brackets += 1
                            elif char == ")":
                                open_brackets -= 1
                            if open_brackets == 0:
                                tokens[0] = tokens[0][:j+1]
                                break
                        attribute += " {}".format(tokens.pop(0))
                    if attribute == "align":
                        attribute += " {}".format(tokens.pop(0))

                    # pop end of argument comma
                    if attribute[-1] == ",":
                        attribute = attribute.rsplit(",", 1)[0]

                    # pop end of argument list bracket
                    if attribute[-1] == ")" and open_brackets == -1:
                        attribute = attribute.rsplit(")", 1)[0]

                    parameter.add_parameter_attribute(attribute)

            # parameter with only parameter type
            # this can be detected by a comma being directly behind the type, or the number of tokens being lower than
            # the token in which the final bracket was found
            if old_tokens[len(old_tokens) - len(tokens) - 1][-1] == "," or len(tokens) < final_bracket_token:
                parameter.set_register("%{}".format(func.get_number_of_parameters()))
                func.add_parameter(parameter)
                continue

            # read parameter name
            if "%" in tokens[0]:
                parameter.set_register(tokens[0].replace(",", "").replace(")", ""))

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
        elif is_function_attribute(tokens[0]):
            if "allocsize" in tokens[0]:
                attribute = tokens.pop(0)
                open_brackets = attribute.count("(") - attribute.count(")")
                while open_brackets != 0:
                    open_brackets += tokens[0].count("(") - tokens[0].count(")")
                    attribute += " {}".format(tokens.pop(0))
                func.add_function_attribute(attribute)
            while is_function_attribute(tokens[0]):
                func.add_function_attribute(tokens[0])
                tokens.pop(0)

        # check section info
        if tokens[0] == "section":
            func.set_section(tokens[1])
            tokens.pop(1)
            tokens.pop(0)

        # check comdat info
        if "comdat" in tokens[0]:
            if "(" in tokens[0]:
                open_brackets = tokens[0].count("(") - tokens[0].count(")")
                value = tokens.pop(0).split("(", 1)[1]
                while open_brackets != 0:
                    value += tokens.pop(0)
                    open_brackets += tokens[0].count("(") - tokens[0].count(")")
                func.set_comdat(value.rsplit(")", 1)[0])
            else:
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
            tokens.pop(0)
            prefix_type, tokens = get_type(tokens)
            prefix_value, tokens = get_value(tokens)
            func.set_prefix("{} {}".format(prefix_type, prefix_value))

        # check prologue info
        if tokens[0] == "prologue":
            tokens.pop(0)
            prologue_type, tokens = get_type(tokens)
            prologue_value, tokens = get_value(tokens)
            func.set_prologue("{} {}".format(prologue_type, prologue_value))

        # check personality info
        if tokens[0] == "personality":
            tokens.pop(0)
            personality_type, tokens = get_type(tokens)
            personality_value, tokens = get_value(tokens)
            func.set_personality("{} {}".format(personality_type, personality_value))

        # check metadata info
        while tokens and is_metadata(tokens[0]):
            func.add_metadata(tokens.pop(0))

        finished = len(tokens) == 1
        if not finished:
            print("analysis did not finish for function: {}".format(func.function_name))
            print(tokens)
        else:
            tokens.pop(0)

        self.functions[func.function_name] = func

        return func.function_name

    def get_function_memory(self, function_name):
        return self.functions[function_name].get_memory()

    def get_function_arguments(self, function_name):
        return self.functions[function_name].get_parameters()

    def get_function(self, function_name):
        return self.functions[function_name]

    def is_startup_func(self, function_name):
        return self.functions[function_name].section == "\".text.startup\""

    def is_mutator(self, function_name):
        return self.functions[function_name].is_mutator()

    def set_mutator(self, function_name):
        self.functions[function_name].set_mutator()

    def add_call(self, function_name, call):
        self.functions[function_name].add_call(call)

    def get_calls(self, function_name):
        return self.functions[function_name].get_calls()

    def add_callbr(self, function_name, callbr):
        self.functions[function_name].add_callbr(callbr)

    def get_callbrs(self, function_name):
        return self.functions[function_name].get_callbrs()

    def add_invoke(self, function_name, invoke):
        self.functions[function_name].add_invoke(invoke)

    def get_invokes(self, function_name):
        return self.functions[function_name].get_invokes()

    def __str__(self):
        result = "The following {} functions were found within the llvm code:\n".format(len(self.functions))
        for key in self.functions:
            result += "{}\n".format(str(self.functions[key]))
        return result


def get_nr_of_tokens_past_last_bracket(tokens):
    open_brackets = 1

    # loop over the tokens until this first bracket is closed again, when this happens, return the index
    for i in range(len(tokens)):
        for j in range(len(tokens[i])):
            char = tokens[i][j]
            if char == "(":
                open_brackets += 1
            elif char == ")":
                open_brackets -= 1
            if open_brackets == 0:
                return len(tokens) - i


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

        self.calls = list()
        self.callbrs = list()
        self.invokes = list()

        self.mutator = False

    def add_call(self, call):
        self.calls.append(call)

    def get_calls(self):
        return self.calls

    def add_calbr(self, callbr):
        self.callbrs.append(callbr)

    def get_callbrs(self):
        return self.callbrs

    def add_invoke(self, invoke):
        self.invokes.append(invoke)

    def get_invokes(self):
        return self.invokes

    def set_linkage_type(self, linkage_type):
        self.linkage_type = linkage_type

    def get_linkage_type(self):
        return self.linkage_type

    def set_runtime_preemption(self, runtime_preemption):
        self.runtime_preemption = runtime_preemption

    def get_runtime_preemption(self):
        return self.runtime_preemption

    def set_visibility_style(self, visibility_style):
        self.visibility_style = visibility_style

    def get_visibility_style(self):
        return self.visibility_style

    def set_dll_storage_class(self, dll_storage_class):
        self.dll_storage_class = dll_storage_class

    def get_dll_storage_class(self):
        return self.dll_storage_class

    def set_calling_convention(self, calling_convention):
        self.calling_convention = calling_convention

    def get_calling_convention(self):
        return self.calling_convention

    def set_unnamed_address(self, unnamed_address):
        self.unnamed_address = unnamed_address

    def get_unnamed_address(self):
        return self.unnamed_address

    def set_return_type(self, return_type):
        self.return_type = return_type

    def get_return_type(self):
        return self.return_type

    def set_return_parameter_attribute(self, return_parameter_attribute):
        self.return_parameter_attribute = return_parameter_attribute

    def get_return_parameter_attribute(self):
        return self.return_parameter_attribute

    def set_function_name(self, function_name):
        self.function_name = function_name

    def get_function_name(self):
        return self.function_name

    def add_parameter(self, parameter):
        self.parameters.append(parameter)

    def set_group_function_attribute(self, group):
        self.function_attributes = group

    def get_function_attribute(self):
        return self.function_attributes

    def add_function_attribute(self, attribute):
        self.function_attributes.append(attribute)

    def set_address_space(self, address_space):
        self.address_space = address_space

    def get_address_space(self):
        return self.address_space

    def set_section(self, section):
        self.section = section

    def get_section(self):
        return self.section

    def set_alignment(self, alignment):
        self.alignment = alignment

    def get_alignment(self):
        return self.alignment

    def set_comdat(self, comdat):
        self.comdat = comdat

    def get_comdat(self):
        return self.comdat

    def set_garbage_collector_name(self, gc_name):
        self.garbage_collector_name = gc_name

    def get_garbage_collector_name(self):
        return self.garbage_collector_name

    def set_prefix(self, prefix):
        self.prefix = prefix

    def get_prefix(self):
        return self.prefix

    def set_prologue(self, prologue):
        self.prologue = prologue

    def get_prologue(self):
        return self.prologue

    def set_personality(self, personality):
        self.personality = personality

    def get_personality(self):
        return self.personality

    def add_metadata(self, metadata):
        self.metadata.append(metadata)

    def get_metadata(self):
        return self.metadata

    def get_number_of_parameters(self):
        return len(self.parameters)

    def get_parameters(self):
        return self.parameters

    def get_memory(self):
        return self.memory

    def is_mutator(self):
        return self.mutator

    def set_mutator(self):
        self.mutator = True

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
        if self.return_parameter_attribute is not None:
            result += "\treturn parameter attribute = {}\n".format(self.return_parameter_attribute)
        if self.return_type is not None:
            result += "\treturn type = {}\n".format(self.return_type)
        if self.function_name is not None:
            result += "\tfunction name = {}\n".format(self.function_name)
        if len(self.parameters) != 0:
            result += "\t{} parameter(s):\n".format(len(self.parameters))
            for parameter in self.parameters:
                result += "\t\t{}\n".format(str(parameter))
        else:
            result += "\t0 parameters\n"
        if self.unnamed_address is not None:
            result += "\tunnamed address = {}\n".format(self.unnamed_address)
        if self.address_space is not None:
            result += "\taddress space = {}\n".format(self.address_space)
        if len(self.function_attributes) != 0:
            result += "\tfunction attributes = {}\n".format(self.function_attributes)
        if self.section is not None:
            result += "\tsection = {}\n".format(self.section)
        if self.comdat is not None:
            result += "\tcomdat = {}\n".format(self.comdat)
        if self.alignment is not None:
            result += "\talignment = {}\n".format(self.alignment)
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

    def is_ret_var(self):
        return "sret" in self.parameter_attributes

    def set_group_parameter_attribute(self, group):
        self.parameter_attributes = group

    def set_register(self, register):
        self.register = register

    def get_register(self):
        return self.register

    def get_parameter_type(self):
        return self.parameter_type

    def get_parameter_attributes(self):
        return self.parameter_attributes

    def __str__(self):
        result = self.parameter_type
        if type(self.parameter_attributes) == list:
            for attr in self.parameter_attributes:
                result += " {}".format(attr)
        else:
            result += self.parameter_attributes
        result += " {}".format(self.register)
        return result
