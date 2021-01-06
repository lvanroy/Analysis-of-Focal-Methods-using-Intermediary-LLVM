import unittest
from llvmAnalyser.terminator.invoke import analyze_invoke


# The ‘invoke’ instruction causes control to transfer to a specified function,
# with the possibility of control flow transfer to either the ‘normal’ label or the ‘exception’ label.
# If the callee function returns with the “ret” instruction, control flow will return to the “normal” label.
# If the callee (or any indirect callees) returns via the “resume” instruction or other exception handling mechanism,
# control is interrupted and continued at the dynamically nearest “exception” label.
#
# The ‘exception’ label is a landing pad for the exception.
# As such, ‘exception’ label is required to have the “landingpad” instruction,
# which contains the information about the behavior of the program after unwinding happens,
# as its first non-PHI instruction. The restrictions on the “landingpad” instruction’s tightly couples it to the
# “invoke” instruction, so that the important information contained within the “landingpad” instruction can’t be
# lost through normal code motion.
#
# <result> = invoke [cconv] [ret attrs] [addrspace(<num>)] <ty>|<fnty> <fnptrval>(<function args>) [fn attrs]
#              [operand bundles] to label <normal label> unwind label <exception label>


class TestLLVMInvoke(unittest.TestCase):
    def test_invoke_no_args(self):
        line = '%1 = invoke cc 10 zeroext addrspace(5) i32 foo() #1 '
        line += '[ "deopt"(i32 10, i32 20), "cold"(), "nonnull"(i64* %val) ] to label %10 unwind label %20'

        invoke = analyze_invoke(line.split(" "))

        self.assertEqual(invoke.get_calling_conv(), "cc 10")
        self.assertEqual(len(invoke.get_ret_attrs()), 1)
        self.assertEqual(invoke.get_ret_attrs()[0], "zeroext")
        self.assertEqual(invoke.get_function_name(), "foo")
        self.assertEqual(len(invoke.get_arguments()), 0)
        self.assertEqual(len(invoke.get_fn_attrs()), 1)
        self.assertEqual(invoke.get_fn_attrs()[0], "#1")
        self.assertEqual(len(invoke.get_operand_bundle_set().get_operand_bundles()), 3)
        self.assertEqual(invoke.get_operand_bundle_set().get_operand_bundles()[0].get_tag(), '"deopt"')
        self.assertEqual(len(invoke.get_operand_bundle_set().get_operand_bundles()[0].get_operands()), 2)
        self.assertEqual(invoke.get_operand_bundle_set().get_operand_bundles()[0].get_operands()[0].get_type(), "i32")
        self.assertEqual(invoke.get_operand_bundle_set().get_operand_bundles()[0].get_operands()[0].get_value(), "10")
        self.assertEqual(invoke.get_operand_bundle_set().get_operand_bundles()[0].get_operands()[1].get_type(), "i32")
        self.assertEqual(invoke.get_operand_bundle_set().get_operand_bundles()[0].get_operands()[1].get_value(), "20")
        self.assertEqual(invoke.get_operand_bundle_set().get_operand_bundles()[1].get_tag(), '"cold"')
        self.assertEqual(len(invoke.get_operand_bundle_set().get_operand_bundles()[1].get_operands()), 0)
        self.assertEqual(invoke.get_operand_bundle_set().get_operand_bundles()[2].get_tag(), '"nonnull"')
        self.assertEqual(len(invoke.get_operand_bundle_set().get_operand_bundles()[2].get_operands()), 1)
        self.assertEqual(invoke.get_operand_bundle_set().get_operand_bundles()[2].get_operands()[0].get_type(), "i64*")
        self.assertEqual(invoke.get_operand_bundle_set().get_operand_bundles()[2].get_operands()[0].get_value(), "%val")
        self.assertEqual(invoke.get_normal(), "%10")
        self.assertEqual(invoke.get_exception(), "%20")

    def test_invoke_many_fn_args(self):
        line = '%1 = invoke cc 10 zeroext addrspace(5) i32 (float, i32) foo(float 5.4, i32 %2) hot convergent '
        line += 'inaccessiblememonly jumptable minsize '
        line += '[ "deopt"(i32 10, i32 20), "cold"(), "nonnull"(i64* %val) ] to label %10 unwind label %20'

        invoke = analyze_invoke(line.split(" "))

        self.assertEqual(invoke.get_calling_conv(), "cc 10")
        self.assertEqual(len(invoke.get_ret_attrs()), 1)
        self.assertEqual(invoke.get_ret_attrs()[0], "zeroext")
        self.assertEqual(invoke.get_function_name(), "foo")
        self.assertEqual(len(invoke.get_arguments()), 2)
        self.assertEqual(invoke.get_arguments()[0].get_register(), "5.4")
        self.assertEqual(invoke.get_arguments()[0].get_parameter_type(), "float")
        self.assertEqual(len(invoke.get_arguments()[0].get_parameter_attributes()), 0)
        self.assertEqual(invoke.get_arguments()[1].get_register(), "%2")
        self.assertEqual(invoke.get_arguments()[1].get_parameter_type(), "i32")
        self.assertEqual(len(invoke.get_arguments()[1].get_parameter_attributes()), 0)
        self.assertEqual(len(invoke.get_fn_attrs()), 5)
        self.assertEqual(invoke.get_fn_attrs()[0], "hot")
        self.assertEqual(invoke.get_fn_attrs()[1], "convergent")
        self.assertEqual(invoke.get_fn_attrs()[2], "inaccessiblememonly")
        self.assertEqual(invoke.get_fn_attrs()[3], "jumptable")
        self.assertEqual(invoke.get_fn_attrs()[4], "minsize")
        self.assertEqual(len(invoke.get_operand_bundle_set().get_operand_bundles()), 3)
        self.assertEqual(invoke.get_operand_bundle_set().get_operand_bundles()[0].get_tag(), '"deopt"')
        self.assertEqual(len(invoke.get_operand_bundle_set().get_operand_bundles()[0].get_operands()), 2)
        self.assertEqual(invoke.get_operand_bundle_set().get_operand_bundles()[0].get_operands()[0].get_type(), "i32")
        self.assertEqual(invoke.get_operand_bundle_set().get_operand_bundles()[0].get_operands()[0].get_value(), "10")
        self.assertEqual(invoke.get_operand_bundle_set().get_operand_bundles()[0].get_operands()[1].get_type(), "i32")
        self.assertEqual(invoke.get_operand_bundle_set().get_operand_bundles()[0].get_operands()[1].get_value(), "20")
        self.assertEqual(invoke.get_operand_bundle_set().get_operand_bundles()[1].get_tag(), '"cold"')
        self.assertEqual(len(invoke.get_operand_bundle_set().get_operand_bundles()[1].get_operands()), 0)
        self.assertEqual(invoke.get_operand_bundle_set().get_operand_bundles()[2].get_tag(), '"nonnull"')
        self.assertEqual(len(invoke.get_operand_bundle_set().get_operand_bundles()[2].get_operands()), 1)
        self.assertEqual(invoke.get_operand_bundle_set().get_operand_bundles()[2].get_operands()[0].get_type(), "i64*")
        self.assertEqual(invoke.get_operand_bundle_set().get_operand_bundles()[2].get_operands()[0].get_value(), "%val")
        self.assertEqual(invoke.get_normal(), "%10")
        self.assertEqual(invoke.get_exception(), "%20")

    def test_invoke_many_args(self):
        line = '%1 = invoke cc 10 zeroext addrspace(5) i32 (float, i32) foo(float 5.4, i32 %2) hot '
        line += '[ "deopt"(i32 10, i32 20), "cold"(), "nonnull"(i64* %val) ] to label %10 unwind label %20'

        invoke = analyze_invoke(line.split(" "))

        self.assertEqual(invoke.get_calling_conv(), "cc 10")
        self.assertEqual(len(invoke.get_ret_attrs()), 1)
        self.assertEqual(invoke.get_ret_attrs()[0], "zeroext")
        self.assertEqual(invoke.get_function_name(), "foo")
        self.assertEqual(len(invoke.get_arguments()), 2)
        self.assertEqual(invoke.get_arguments()[0].get_register(), "5.4")
        self.assertEqual(invoke.get_arguments()[0].get_parameter_type(), "float")
        self.assertEqual(len(invoke.get_arguments()[0].get_parameter_attributes()), 0)
        self.assertEqual(invoke.get_arguments()[1].get_register(), "%2")
        self.assertEqual(invoke.get_arguments()[1].get_parameter_type(), "i32")
        self.assertEqual(len(invoke.get_arguments()[1].get_parameter_attributes()), 0)
        self.assertEqual(len(invoke.get_fn_attrs()), 1)
        self.assertEqual(invoke.get_fn_attrs()[0], "hot")
        self.assertEqual(len(invoke.get_operand_bundle_set().get_operand_bundles()), 3)
        self.assertEqual(invoke.get_operand_bundle_set().get_operand_bundles()[0].get_tag(), '"deopt"')
        self.assertEqual(len(invoke.get_operand_bundle_set().get_operand_bundles()[0].get_operands()), 2)
        self.assertEqual(invoke.get_operand_bundle_set().get_operand_bundles()[0].get_operands()[0].get_type(), "i32")
        self.assertEqual(invoke.get_operand_bundle_set().get_operand_bundles()[0].get_operands()[0].get_value(), "10")
        self.assertEqual(invoke.get_operand_bundle_set().get_operand_bundles()[0].get_operands()[1].get_type(), "i32")
        self.assertEqual(invoke.get_operand_bundle_set().get_operand_bundles()[0].get_operands()[1].get_value(), "20")
        self.assertEqual(invoke.get_operand_bundle_set().get_operand_bundles()[1].get_tag(), '"cold"')
        self.assertEqual(len(invoke.get_operand_bundle_set().get_operand_bundles()[1].get_operands()), 0)
        self.assertEqual(invoke.get_operand_bundle_set().get_operand_bundles()[2].get_tag(), '"nonnull"')
        self.assertEqual(len(invoke.get_operand_bundle_set().get_operand_bundles()[2].get_operands()), 1)
        self.assertEqual(invoke.get_operand_bundle_set().get_operand_bundles()[2].get_operands()[0].get_type(), "i64*")
        self.assertEqual(invoke.get_operand_bundle_set().get_operand_bundles()[2].get_operands()[0].get_value(), "%val")
        self.assertEqual(invoke.get_normal(), "%10")
        self.assertEqual(invoke.get_exception(), "%20")

    def test_call_many_args_with_param_attrs(self):
        line = '%1 = invoke cc 10 zeroext addrspace(5) i32 (float, i32) foo(float 5.4, i32 '
        line += 'align 8 noalias sret(i8) dereferenceable(20) immarg %2) hot '
        line += '[ "deopt"(i32 10, i32 20), "cold"(), "nonnull"(i64* %val) ] to label %10 unwind label %20'

        invoke = analyze_invoke(line.split(" "))

        self.assertEqual(invoke.get_calling_conv(), "cc 10")
        self.assertEqual(len(invoke.get_ret_attrs()), 1)
        self.assertEqual(invoke.get_ret_attrs()[0], "zeroext")
        self.assertEqual(invoke.get_function_name(), "foo")
        self.assertEqual(len(invoke.get_arguments()), 2)
        self.assertEqual(invoke.get_arguments()[0].get_register(), "5.4")
        self.assertEqual(invoke.get_arguments()[0].get_parameter_type(), "float")
        self.assertEqual(len(invoke.get_arguments()[0].get_parameter_attributes()), 0)
        self.assertEqual(invoke.get_arguments()[1].get_register(), "%2")
        self.assertEqual(invoke.get_arguments()[1].get_parameter_type(), "i32")
        self.assertEqual(len(invoke.get_arguments()[1].get_parameter_attributes()), 5)
        self.assertEqual(invoke.get_arguments()[1].get_parameter_attributes()[0], "align 8")
        self.assertEqual(invoke.get_arguments()[1].get_parameter_attributes()[1], "noalias")
        self.assertEqual(invoke.get_arguments()[1].get_parameter_attributes()[2], "sret(i8)")
        self.assertEqual(invoke.get_arguments()[1].get_parameter_attributes()[3], "dereferenceable(20)")
        self.assertEqual(invoke.get_arguments()[1].get_parameter_attributes()[4], "immarg")
        self.assertEqual(len(invoke.get_fn_attrs()), 1)
        self.assertEqual(invoke.get_fn_attrs()[0], "hot")
        self.assertEqual(len(invoke.get_operand_bundle_set().get_operand_bundles()), 3)
        self.assertEqual(invoke.get_operand_bundle_set().get_operand_bundles()[0].get_tag(), '"deopt"')
        self.assertEqual(len(invoke.get_operand_bundle_set().get_operand_bundles()[0].get_operands()), 2)
        self.assertEqual(invoke.get_operand_bundle_set().get_operand_bundles()[0].get_operands()[0].get_type(), "i32")
        self.assertEqual(invoke.get_operand_bundle_set().get_operand_bundles()[0].get_operands()[0].get_value(), "10")
        self.assertEqual(invoke.get_operand_bundle_set().get_operand_bundles()[0].get_operands()[1].get_type(), "i32")
        self.assertEqual(invoke.get_operand_bundle_set().get_operand_bundles()[0].get_operands()[1].get_value(), "20")
        self.assertEqual(invoke.get_operand_bundle_set().get_operand_bundles()[1].get_tag(), '"cold"')
        self.assertEqual(len(invoke.get_operand_bundle_set().get_operand_bundles()[1].get_operands()), 0)
        self.assertEqual(invoke.get_operand_bundle_set().get_operand_bundles()[2].get_tag(), '"nonnull"')
        self.assertEqual(len(invoke.get_operand_bundle_set().get_operand_bundles()[2].get_operands()), 1)
        self.assertEqual(invoke.get_operand_bundle_set().get_operand_bundles()[2].get_operands()[0].get_type(), "i64*")
        self.assertEqual(invoke.get_operand_bundle_set().get_operand_bundles()[2].get_operands()[0].get_value(), "%val")
        self.assertEqual(invoke.get_normal(), "%10")
        self.assertEqual(invoke.get_exception(), "%20")
