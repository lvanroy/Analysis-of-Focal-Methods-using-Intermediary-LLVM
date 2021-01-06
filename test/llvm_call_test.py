import unittest
from llvmAnalyser.other.call import analyze_call
# The ‘call’ instruction represents a simple function call.

# <result> = [tail | musttail | notail ] call [fast-math flags] [cconv] [ret attrs] [addrspace(<num>)]
#            <ty>|<fnty> <fnptrval>(<function args>) [fn attrs] [ operand bundles ]


class TestLLVMCall(unittest.TestCase):
    def test_call_no_args(self):
        line = '%1 = tail call nnan cc 10 zeroext inreg addrspace(2) i32 @foo() allocsize(4, 8) '
        line += '[ "deopt"(i32 10, i32 20), "cold"(), "nonnull"(i64* %val) ]'

        call = analyze_call(line.split(" "))

        self.assertEqual(call.get_calling_convention(), "cc 10")
        self.assertEqual(len(call.get_return_attrs()), 2)
        self.assertEqual(call.get_return_attrs()[0], "zeroext")
        self.assertEqual(call.get_return_attrs()[1], "inreg")
        self.assertEqual(call.get_function_name(), "@foo")
        self.assertEqual(len(call.get_arguments()), 0)
        self.assertEqual(len(call.get_function_attributes()), 1)
        self.assertEqual(call.get_function_attributes()[0], "allocsize(4, 8)")
        self.assertEqual(len(call.get_operand_bundle_set().get_operand_bundles()), 3)
        self.assertEqual(call.get_operand_bundle_set().get_operand_bundles()[0].get_tag(), '"deopt"')
        self.assertEqual(len(call.get_operand_bundle_set().get_operand_bundles()[0].get_operands()), 2)
        self.assertEqual(call.get_operand_bundle_set().get_operand_bundles()[0].get_operands()[0].get_type(), "i32")
        self.assertEqual(call.get_operand_bundle_set().get_operand_bundles()[0].get_operands()[0].get_value(), "10")
        self.assertEqual(call.get_operand_bundle_set().get_operand_bundles()[0].get_operands()[1].get_type(), "i32")
        self.assertEqual(call.get_operand_bundle_set().get_operand_bundles()[0].get_operands()[1].get_value(), "20")
        self.assertEqual(call.get_operand_bundle_set().get_operand_bundles()[1].get_tag(), '"cold"')
        self.assertEqual(len(call.get_operand_bundle_set().get_operand_bundles()[1].get_operands()), 0)
        self.assertEqual(call.get_operand_bundle_set().get_operand_bundles()[2].get_tag(), '"nonnull"')
        self.assertEqual(len(call.get_operand_bundle_set().get_operand_bundles()[2].get_operands()), 1)
        self.assertEqual(call.get_operand_bundle_set().get_operand_bundles()[2].get_operands()[0].get_type(), "i64*")
        self.assertEqual(call.get_operand_bundle_set().get_operand_bundles()[2].get_operands()[0].get_value(), "%val")

    def test_call_many_fn_args(self):
        line = '%1 = tail call nnan cc 10 zeroext inreg #2 i32 @foo() allocsize(4, 8) '
        line += 'noinline alignstack(4) inaccessiblemem_or_argmemonly '
        line += '"no-inline-line-tables" "probe-stack" "patchable-function" '
        line += '[ "deopt"(i32 10, i32 20), "cold"(), "nonnull"(i64* %val) ]'

        call = analyze_call(line.split(" "))

        self.assertEqual(call.get_calling_convention(), "cc 10")
        self.assertEqual(len(call.get_return_attrs()), 2)
        self.assertEqual(call.get_return_attrs()[0], "zeroext")
        self.assertEqual(call.get_return_attrs()[1], "inreg")
        self.assertEqual(call.get_function_name(), "@foo")
        self.assertEqual(len(call.get_arguments()), 0)
        self.assertEqual(len(call.get_function_attributes()), 7)
        self.assertEqual(call.get_function_attributes()[0], "allocsize(4, 8)")
        self.assertEqual(call.get_function_attributes()[1], "noinline")
        self.assertEqual(call.get_function_attributes()[2], "alignstack(4)")
        self.assertEqual(call.get_function_attributes()[3], "inaccessiblemem_or_argmemonly")
        self.assertEqual(call.get_function_attributes()[4], '"no-inline-line-tables"')
        self.assertEqual(call.get_function_attributes()[5], '"probe-stack"')
        self.assertEqual(call.get_function_attributes()[6], '"patchable-function"')
        self.assertEqual(len(call.get_operand_bundle_set().get_operand_bundles()), 3)
        self.assertEqual(call.get_operand_bundle_set().get_operand_bundles()[0].get_tag(), '"deopt"')
        self.assertEqual(len(call.get_operand_bundle_set().get_operand_bundles()[0].get_operands()), 2)
        self.assertEqual(call.get_operand_bundle_set().get_operand_bundles()[0].get_operands()[0].get_type(), "i32")
        self.assertEqual(call.get_operand_bundle_set().get_operand_bundles()[0].get_operands()[0].get_value(), "10")
        self.assertEqual(call.get_operand_bundle_set().get_operand_bundles()[0].get_operands()[1].get_type(), "i32")
        self.assertEqual(call.get_operand_bundle_set().get_operand_bundles()[0].get_operands()[1].get_value(), "20")
        self.assertEqual(call.get_operand_bundle_set().get_operand_bundles()[1].get_tag(), '"cold"')
        self.assertEqual(len(call.get_operand_bundle_set().get_operand_bundles()[1].get_operands()), 0)
        self.assertEqual(call.get_operand_bundle_set().get_operand_bundles()[2].get_tag(), '"nonnull"')
        self.assertEqual(len(call.get_operand_bundle_set().get_operand_bundles()[2].get_operands()), 1)
        self.assertEqual(call.get_operand_bundle_set().get_operand_bundles()[2].get_operands()[0].get_type(), "i64*")
        self.assertEqual(call.get_operand_bundle_set().get_operand_bundles()[2].get_operands()[0].get_value(), "%val")

    def test_call_many_args(self):
        line = '%1 = tail call nnan cc 10 zeroext inreg #2 i32 @foo(i32 20, i8 %val) allocsize(4, 8) '
        line += '[ "deopt"(i32 10, i32 20), "cold"(), "nonnull"(i64* %val) ]'

        call = analyze_call(line.split(" "))

        self.assertEqual(call.get_calling_convention(), "cc 10")
        self.assertEqual(len(call.get_return_attrs()), 2)
        self.assertEqual(call.get_return_attrs()[0], "zeroext")
        self.assertEqual(call.get_return_attrs()[1], "inreg")
        self.assertEqual(call.get_function_name(), "@foo")
        self.assertEqual(len(call.get_arguments()), 2)
        self.assertEqual(call.get_arguments()[0].get_parameter_type(), "i32")
        self.assertEqual(call.get_arguments()[0].get_register(), "20")
        self.assertEqual(len(call.get_arguments()[0].get_parameter_attributes()), 0)
        self.assertEqual(call.get_arguments()[1].get_parameter_type(), "i8")
        self.assertEqual(call.get_arguments()[1].get_register(), "%val")
        self.assertEqual(len(call.get_arguments()[1].get_parameter_attributes()), 0)
        self.assertEqual(len(call.get_function_attributes()), 1)
        self.assertEqual(call.get_function_attributes()[0], "allocsize(4, 8)")
        self.assertEqual(len(call.get_operand_bundle_set().get_operand_bundles()), 3)
        self.assertEqual(call.get_operand_bundle_set().get_operand_bundles()[0].get_tag(), '"deopt"')
        self.assertEqual(len(call.get_operand_bundle_set().get_operand_bundles()[0].get_operands()), 2)
        self.assertEqual(call.get_operand_bundle_set().get_operand_bundles()[0].get_operands()[0].get_type(), "i32")
        self.assertEqual(call.get_operand_bundle_set().get_operand_bundles()[0].get_operands()[0].get_value(), "10")
        self.assertEqual(call.get_operand_bundle_set().get_operand_bundles()[0].get_operands()[1].get_type(), "i32")
        self.assertEqual(call.get_operand_bundle_set().get_operand_bundles()[0].get_operands()[1].get_value(), "20")
        self.assertEqual(call.get_operand_bundle_set().get_operand_bundles()[1].get_tag(), '"cold"')
        self.assertEqual(len(call.get_operand_bundle_set().get_operand_bundles()[1].get_operands()), 0)
        self.assertEqual(call.get_operand_bundle_set().get_operand_bundles()[2].get_tag(), '"nonnull"')
        self.assertEqual(len(call.get_operand_bundle_set().get_operand_bundles()[2].get_operands()), 1)
        self.assertEqual(call.get_operand_bundle_set().get_operand_bundles()[2].get_operands()[0].get_type(), "i64*")
        self.assertEqual(call.get_operand_bundle_set().get_operand_bundles()[2].get_operands()[0].get_value(), "%val")

    def test_call_many_args_with_param_attrs(self):
        line = '%1 = tail call nnan cc 10 zeroext inreg #2 i32 @foo(i32 20, '
        line += 'i8* align 8 noalias sret(i8) dereferenceable(20) immarg %val) allocsize(4, 8) '
        line += '[ "deopt"(i32 10, i32 20), "cold"(), "nonnull"(i64* %val) ]'

        call = analyze_call(line.split(" "))

        self.assertEqual(call.get_calling_convention(), "cc 10")
        self.assertEqual(len(call.get_return_attrs()), 2)
        self.assertEqual(call.get_return_attrs()[0], "zeroext")
        self.assertEqual(call.get_return_attrs()[1], "inreg")
        self.assertEqual(call.get_function_name(), "@foo")
        self.assertEqual(len(call.get_arguments()), 2)
        self.assertEqual(call.get_arguments()[0].get_parameter_type(), "i32")
        self.assertEqual(call.get_arguments()[0].get_register(), "20")
        self.assertEqual(len(call.get_arguments()[0].get_parameter_attributes()), 0)
        self.assertEqual(call.get_arguments()[1].get_parameter_type(), "i8*")
        self.assertEqual(call.get_arguments()[1].get_register(), "%val")
        self.assertEqual(len(call.get_arguments()[1].get_parameter_attributes()), 5)
        self.assertEqual(call.get_arguments()[1].get_parameter_attributes()[0], "align 8")
        self.assertEqual(call.get_arguments()[1].get_parameter_attributes()[1], "noalias")
        self.assertEqual(call.get_arguments()[1].get_parameter_attributes()[2], "sret(i8)")
        self.assertEqual(call.get_arguments()[1].get_parameter_attributes()[3], "dereferenceable(20)")
        self.assertEqual(call.get_arguments()[1].get_parameter_attributes()[4], "immarg")
        self.assertEqual(len(call.get_function_attributes()), 1)
        self.assertEqual(call.get_function_attributes()[0], "allocsize(4, 8)")
        self.assertEqual(len(call.get_operand_bundle_set().get_operand_bundles()), 3)
        self.assertEqual(call.get_operand_bundle_set().get_operand_bundles()[0].get_tag(), '"deopt"')
        self.assertEqual(len(call.get_operand_bundle_set().get_operand_bundles()[0].get_operands()), 2)
        self.assertEqual(call.get_operand_bundle_set().get_operand_bundles()[0].get_operands()[0].get_type(), "i32")
        self.assertEqual(call.get_operand_bundle_set().get_operand_bundles()[0].get_operands()[0].get_value(), "10")
        self.assertEqual(call.get_operand_bundle_set().get_operand_bundles()[0].get_operands()[1].get_type(), "i32")
        self.assertEqual(call.get_operand_bundle_set().get_operand_bundles()[0].get_operands()[1].get_value(), "20")
        self.assertEqual(call.get_operand_bundle_set().get_operand_bundles()[1].get_tag(), '"cold"')
        self.assertEqual(len(call.get_operand_bundle_set().get_operand_bundles()[1].get_operands()), 0)
        self.assertEqual(call.get_operand_bundle_set().get_operand_bundles()[2].get_tag(), '"nonnull"')
        self.assertEqual(len(call.get_operand_bundle_set().get_operand_bundles()[2].get_operands()), 1)
        self.assertEqual(call.get_operand_bundle_set().get_operand_bundles()[2].get_operands()[0].get_type(), "i64*")
        self.assertEqual(call.get_operand_bundle_set().get_operand_bundles()[2].get_operands()[0].get_value(), "%val")

