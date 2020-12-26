import unittest
from llvmAnalyser.function import FunctionHandler
# LLVM function definitions consist of the “define” keyword, an optional linkage type,
# an optional runtime preemption specifier, an optional visibility style, an optional DLL storage class,
# an optional calling convention, an optional unnamed_addr attribute, a return type,
# an optional parameter attribute for the return type, a function name,
# a (possibly empty) argument list (each with optional parameter attributes), optional function attributes,
# an optional address space, an optional section, an optional alignment,
# an optional comdat, an optional garbage collector name, an optional prefix, an optional prologue,
# an optional personality, an optional list of attached metadata, an opening curly brace, a list of basic blocks,
# and a closing curly brace.

# define [linkage] [PreemptionSpecifier] [visibility] [DLLStorageClass](
#        [cconv] [ret attrs]
#        <ResultType> @<FunctionName> ([argument list])
#        [(unnamed_addr|local_unnamed_addr)] [AddrSpace] [fn Attrs]
#        [section "name"] [comdat [($name)]] [align N] [gc] [prefix Constant]
#        [prologue Constant] [personality Constant] (!name !N)* { ... }


class TestLLVMDecl(unittest.TestCase):
    def test_decl_no_args(self):
        handler = FunctionHandler()

        line = 'define private dso_preemptable protected dllimport cc 10 align 8 %"class.std::shared_ptr.30"* '
        line += 'foo() unnamed_addr #6 allocsize(4, 8) section ".text.startup" comdat(foo) align 8 gc "Erlang" '
        line += 'prefix i32 4 prologue i8 144 personality i8* bitcast (i32 (...)* @__gxx_personality_v0 to i8*) !foo {'

        function_name = handler.identify_function(line.split(" "))

        function = handler.get_function(function_name)

        self.assertEqual(function.get_linkage_type(), "private")
        self.assertEqual(function.get_runtime_preemption(), "dso_preemptable")
        self.assertEqual(function.get_visibility_style(), "protected")
        self.assertEqual(function.get_dll_storage_class(), "dllimport")
        self.assertEqual(function.get_calling_convention(), "cc 10")
        self.assertEqual(function.get_return_parameter_attribute(), "align 8")
        self.assertEqual(function.get_return_type(), '%"class.std::shared_ptr.30"*')
        self.assertEqual(function.get_function_name(), "foo")
        self.assertEqual(function.get_number_of_parameters(), 0)
        self.assertEqual(function.get_unnamed_address(), "unnamed_addr")
        self.assertEqual(function.get_address_space(), "#6")
        self.assertEqual(function.get_function_attribute()[0], "allocsize(4, 8)")
        self.assertEqual(len(function.get_function_attribute()), 1)
        self.assertEqual(function.get_section(), '".text.startup"')
        self.assertEqual(function.get_comdat(), "foo")
        self.assertEqual(function.get_alignment(), "8")
        self.assertEqual(function.get_garbage_collector_name(), '"Erlang"')
        self.assertEqual(function.get_prefix(), "i32 4")
        self.assertEqual(function.get_prologue(), "i8 144")
        self.assertEqual(function.get_personality(), "i8* bitcast i32 (...)* @__gxx_personality_v0 to i8*")
        self.assertEqual(function.get_metadata()[0], "!foo")
        self.assertEqual(len(function.get_metadata()), 1)

    def test_decl_many_func_attrs(self):
        handler = FunctionHandler()

        line = 'define private dso_preemptable protected dllimport cc 10 align 8 %"class.std::shared_ptr.30"* '
        line += 'foo() unnamed_addr #6 allocsize(4, 8) alignstack(4) inaccessiblemem_or_argmemonly '
        line += '"no-inline-line-tables" "probe-stack" "patchable-function" '
        line += 'section ".text.startup" comdat(foo) align 8 gc "Erlang" '
        line += 'prefix i32 4 prologue i8 144 personality i8* bitcast (i32 (...)* @__gxx_personality_v0 to i8*) !foo {'

        function_name = handler.identify_function(line.split(" "))

        function = handler.get_function(function_name)

        self.assertEqual(function.get_linkage_type(), "private")
        self.assertEqual(function.get_runtime_preemption(), "dso_preemptable")
        self.assertEqual(function.get_visibility_style(), "protected")
        self.assertEqual(function.get_dll_storage_class(), "dllimport")
        self.assertEqual(function.get_calling_convention(), "cc 10")
        self.assertEqual(function.get_return_parameter_attribute(), "align 8")
        self.assertEqual(function.get_return_type(), '%"class.std::shared_ptr.30"*')
        self.assertEqual(function.get_function_name(), "foo")
        self.assertEqual(function.get_number_of_parameters(), 0)
        self.assertEqual(function.get_unnamed_address(), "unnamed_addr")
        self.assertEqual(function.get_address_space(), "#6")
        self.assertEqual(function.get_function_attribute()[0], "allocsize(4, 8)")
        self.assertEqual(function.get_function_attribute()[1], "alignstack(4)")
        self.assertEqual(function.get_function_attribute()[2], "inaccessiblemem_or_argmemonly")
        self.assertEqual(function.get_function_attribute()[3], '"no-inline-line-tables"')
        self.assertEqual(function.get_function_attribute()[4], '"probe-stack"')
        self.assertEqual(function.get_function_attribute()[5], '"patchable-function"')
        self.assertEqual(len(function.get_function_attribute()), 6)
        self.assertEqual(function.get_section(), '".text.startup"')
        self.assertEqual(function.get_comdat(), "foo")
        self.assertEqual(function.get_alignment(), "8")
        self.assertEqual(function.get_garbage_collector_name(), '"Erlang"')
        self.assertEqual(function.get_prefix(), "i32 4")
        self.assertEqual(function.get_prologue(), "i8 144")
        self.assertEqual(function.get_personality(), "i8* bitcast i32 (...)* @__gxx_personality_v0 to i8*")
        self.assertEqual(function.get_metadata()[0], "!foo")
        self.assertEqual(len(function.get_metadata()), 1)

    def test_decl_no_arg_attributes(self):
        handler = FunctionHandler()

        line = 'define private dso_preemptable protected dllimport cc 10 align 8 %"class.std::shared_ptr.30"* '
        line += 'foo(i32 %0, i8 %1) unnamed_addr #6 allocsize(4, 8) section ".text.startup" comdat(foo) align 8 '
        line += 'gc "Erlang" prefix i32 4 prologue i8 144 '
        line += 'personality i8* bitcast (i32 (...)* @__gxx_personality_v0 to i8*) !foo {'

        function_name = handler.identify_function(line.split(" "))

        function = handler.get_function(function_name)

        self.assertEqual(function.get_linkage_type(), "private")
        self.assertEqual(function.get_runtime_preemption(), "dso_preemptable")
        self.assertEqual(function.get_visibility_style(), "protected")
        self.assertEqual(function.get_dll_storage_class(), "dllimport")
        self.assertEqual(function.get_calling_convention(), "cc 10")
        self.assertEqual(function.get_return_parameter_attribute(), "align 8")
        self.assertEqual(function.get_return_type(), '%"class.std::shared_ptr.30"*')
        self.assertEqual(function.get_function_name(), "foo")
        self.assertEqual(function.get_number_of_parameters(), 2)
        self.assertEqual(function.get_parameters()[0].get_register(), "%0")
        self.assertEqual(function.get_parameters()[0].get_parameter_type(), "i32")
        self.assertEqual(function.get_parameters()[0].get_parameter_attributes(), list())
        self.assertEqual(function.get_parameters()[1].get_register(), "%1")
        self.assertEqual(function.get_parameters()[1].get_parameter_type(), "i8")
        self.assertEqual(function.get_parameters()[1].get_parameter_attributes(), list())
        self.assertEqual(function.get_unnamed_address(), "unnamed_addr")
        self.assertEqual(function.get_address_space(), "#6")
        self.assertEqual(function.get_function_attribute()[0], "allocsize(4, 8)")
        self.assertEqual(len(function.get_function_attribute()), 1)
        self.assertEqual(function.get_section(), '".text.startup"')
        self.assertEqual(function.get_comdat(), "foo")
        self.assertEqual(function.get_alignment(), "8")
        self.assertEqual(function.get_garbage_collector_name(), '"Erlang"')
        self.assertEqual(function.get_prefix(), "i32 4")
        self.assertEqual(function.get_prologue(), "i8 144")
        self.assertEqual(function.get_personality(), "i8* bitcast i32 (...)* @__gxx_personality_v0 to i8*")
        self.assertEqual(function.get_metadata()[0], "!foo")
        self.assertEqual(len(function.get_metadata()), 1)

    def test_decl_with_arg_attributes(self):
        handler = FunctionHandler()

        line = 'define private dso_preemptable protected dllimport cc 10 align 8 %"class.std::shared_ptr.30"* '
        line += 'foo(i32 zeroext byref(i32) sret %0, i8 align 8 dereferenceable_or_null(8) %1) '
        line += 'unnamed_addr #6 allocsize(4, 8) section ".text.startup" comdat(foo) align 8 '
        line += 'gc "Erlang" prefix i32 4 prologue i8 144 '
        line += 'personality i8* bitcast (i32 (...)* @__gxx_personality_v0 to i8*) !foo {'

        function_name = handler.identify_function(line.split(" "))

        function = handler.get_function(function_name)

        self.assertEqual(function.get_linkage_type(), "private")
        self.assertEqual(function.get_runtime_preemption(), "dso_preemptable")
        self.assertEqual(function.get_visibility_style(), "protected")
        self.assertEqual(function.get_dll_storage_class(), "dllimport")
        self.assertEqual(function.get_calling_convention(), "cc 10")
        self.assertEqual(function.get_return_parameter_attribute(), "align 8")
        self.assertEqual(function.get_return_type(), '%"class.std::shared_ptr.30"*')
        self.assertEqual(function.get_function_name(), "foo")
        self.assertEqual(function.get_number_of_parameters(), 2)
        self.assertEqual(function.get_parameters()[0].get_register(), "%0")
        self.assertEqual(function.get_parameters()[0].get_parameter_type(), "i32")
        self.assertEqual(function.get_parameters()[0].get_parameter_attributes(), ["zeroext", "byref(i32)", "sret"])
        self.assertEqual(function.get_parameters()[1].get_register(), "%1")
        self.assertEqual(function.get_parameters()[1].get_parameter_type(), "i8")
        self.assertEqual(function.get_parameters()[1].get_parameter_attributes(),
                         ["align 8", "dereferenceable_or_null(8)"])
        self.assertEqual(function.get_unnamed_address(), "unnamed_addr")
        self.assertEqual(function.get_address_space(), "#6")
        self.assertEqual(function.get_function_attribute()[0], "allocsize(4, 8)")
        self.assertEqual(len(function.get_function_attribute()), 1)
        self.assertEqual(function.get_section(), '".text.startup"')
        self.assertEqual(function.get_comdat(), "foo")
        self.assertEqual(function.get_alignment(), "8")
        self.assertEqual(function.get_garbage_collector_name(), '"Erlang"')
        self.assertEqual(function.get_prefix(), "i32 4")
        self.assertEqual(function.get_prologue(), "i8 144")
        self.assertEqual(function.get_personality(), "i8* bitcast i32 (...)* @__gxx_personality_v0 to i8*")
        self.assertEqual(function.get_metadata()[0], "!foo")
        self.assertEqual(len(function.get_metadata()), 1)
