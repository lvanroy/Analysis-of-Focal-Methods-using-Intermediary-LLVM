import unittest
from llvmAnalyser.values import get_value


class TestLLVMValues(unittest.TestCase):
    def test_registers(self):
        self.assertEqual(get_value(["%10"])[0], "%10")
        self.assertEqual(get_value(["%value"])[0], "%value")
        self.assertEqual(get_value(["%5,", "i32", "%6)"])[0], "%5")
        self.assertEqual(get_value(["%5)"])[0], "%5")

    def test_boolean_constants(self):
        self.assertEqual(get_value(["true"])[0], "true")
        self.assertEqual(get_value(["false"])[0], "false")
        self.assertEqual(get_value(["true,", "i1", "false"])[0], "true")
        self.assertEqual(get_value(["true)"])[0], "true")

    def test_numeric_constants(self):
        self.assertEqual(get_value(["123"])[0], "123")
        self.assertEqual(get_value(["-4"])[0], "-4")
        self.assertEqual(get_value(["123.321"])[0], "123.321")
        self.assertEqual(get_value(["1.23321e+2"])[0], "1.23321e+2")
        self.assertEqual(get_value(["1.23321e+2,", "i1", "false"])[0], "1.23321e+2")
        self.assertEqual(get_value(["1.23321e+2)"])[0], "1.23321e+2")

    def test_hex_numeric_constants(self):
        self.assertEqual(get_value(["0x432ff973cafa8000"])[0], "0x432ff973cafa8000")
        self.assertEqual(get_value(["0x432ff973cafa323,", "i1", "true"])[0], "0x432ff973cafa323")
        self.assertEqual(get_value(["0x432ff973cafa323)"])[0], "0x432ff973cafa323")

    def test_null_none_undef(self):
        self.assertEqual(get_value(["null"])[0], "null")
        self.assertEqual(get_value(["none"])[0], "none")
        self.assertEqual(get_value(["undef"])[0], "undef")
        self.assertEqual(get_value(["null,", "i1", "false"])[0], "null")
        self.assertEqual(get_value(["null)"])[0], "null")

    def test_structure_constants(self):
        self.assertEqual(get_value(["{", "i32", "4,", "float", "17.0,", "i32*", "@G", "}"])[0],
                         "{ i32 4, float 17.0, i32* @G }")
        self.assertEqual(get_value(["{i32", "4,", "float", "17.0})"])[0], "{i32 4, float 17.0}")
        self.assertEqual(get_value(["{i32", "4,", "float", "17.0},", "i32", "5", ")"])[0], "{i32 4, float 17.0}")

    def test_array_constants(self):
        self.assertEqual(get_value(["[i32", "42,", "i32", "11,", "i32", "74]"])[0], "[i32 42, i32 11, i32 74]")
        self.assertEqual(get_value(["[i32", "4],", "i32", "4)"])[0], "[i32 4]")
        self.assertEqual(get_value(["[i32", "4])"])[0], "[i32 4]")

    def test_vector_constants(self):
        self.assertEqual(get_value(["<i32", "42,", "i32", "11,", "i32", "74,", "i32", "100>"])[0],
                         "<i32 42, i32 11, i32 74, i32 100>")
        self.assertEqual(get_value(["<i32", "42>,", "i32", "0)"])[0], "<i32 42>")
        self.assertEqual(get_value(["<i32", "42>)"])[0], "<i32 42>")

    def test_zero_initialization(self):
        self.assertEqual(get_value(["zeroinitializer"])[0], "zeroinitializer")
        self.assertEqual(get_value(["zeroinitializer,", "i32", "4)"])[0], "zeroinitializer")
        self.assertEqual(get_value(["zeroinitializer)"])[0], "zeroinitializer")

    def test_metadata(self):
        self.assertEqual(get_value(["!{!0,", "!{!2,", "!0},", "!\"test\"}"])[0], "!{!0, !{!2, !0}, !\"test\"}")
        self.assertEqual(
            get_value(["!{!0,", "i32", "0,", "i8*", "@global,", "i64", "(i64)*", "@function,", "!\"str\"}"])[0],
            "!{!0, i32 0, i8* @global, i64 (i64)* @function, !\"str\"}")

    def test_global_var(self):
        self.assertEqual(get_value(["@A"])[0], "@A")
        self.assertEqual(get_value(["@str.1"])[0], "@str.1")
        self.assertEqual(get_value(["@_class_Profile"])[0], "@_class_Profile")
        self.assertEqual(get_value(["@_class_Profile,", "i32", "4)"])[0], "@_class_Profile")
        self.assertEqual(get_value(["@str.1)"])[0], "@str.1")

    def test_blockaddress(self):
        self.assertEqual(get_value(["blockaddress(@function,", "%block)"])[0], "blockaddress(@function, %block)")

    def test_const_conversion(self):
        result = get_value(["trunc", "i32", "257", "to", "i8"])
        self.assertEqual(result[0], "trunc i32 257 to i8")

        result = get_value(["zext", "<2", "x", "i16>", "<i16", "8,", "i16", "7>", "to", "<2", "x", "i32>"])
        self.assertEqual(result[0], "zext <2 x i16> <i16 8, i16 7> to <2 x i32>")

        result = get_value(["sext", "i8", "-1", "to", "i16", "i32", "5"])
        self.assertEqual(result[0], "sext i8 -1 to i16")
        self.assertEqual(result[1], ["i32", "5"])

        result = get_value(["fptrunc",  "double", "16777217.0", "to", "float"])
        self.assertEqual(result[0], "fptrunc double 16777217.0 to float")

        result = get_value(["fpext", "double", "%X", "to", "fp128"])
        self.assertEqual(result[0], "fpext double %X to fp128")

        result = get_value(["fptoui", "float", "1.04E+17", "to", "i8"])
        self.assertEqual(result[0], "fptoui float 1.04E+17 to i8")

        result = get_value(["fptosi", "float", "1.0E-247", "to", "i1"])
        self.assertEqual(result[0], "fptosi float 1.0E-247 to i1")

        result = get_value(["uitofp", "i8", "-1", "to", "double"])
        self.assertEqual(result[0], "uitofp i8 -1 to double")

        result = get_value(["sitofp", "i8", "-1", "to", "double"])
        self.assertEqual(result[0], "sitofp i8 -1 to double")

        result = get_value(["ptrtoint", "<4", "x", "i32*>", "%P", "to", "<4", "x", "i64>"])
        self.assertEqual(result[0], "ptrtoint <4 x i32*> %P to <4 x i64>")

        result = get_value(["inttoptr", "<4", "x", "i32>", "%G", "to", "<4", "x", "i8*>"])
        self.assertEqual(result[0], "inttoptr <4 x i32> %G to <4 x i8*>")

        result = get_value(["bitcast", "<2", "x", "i32*>", "%V", "to", "<2", "x", "i64*>"])
        self.assertEqual(result[0], "bitcast <2 x i32*> %V to <2 x i64*>")

        result = get_value(["addrspacecast", "<4 x i32*>", "%z", "to", "<4", "x", "float", "addrspace(3)*>"])
        self.assertEqual(result[0], "addrspacecast <4 x i32*> %z to <4 x float addrspace(3)*>")

    def test_const_getelementptr(self):
        result = get_value(["getelementptr", "inbounds", "[5", "x", "i8*],", "[5", "x", "i8*]*", "@_ZTV9Rectangle,",
                            "i32", "0,", "i32", "2"])
        self.assertEqual(result[0], "getelementptr inbounds [5 x i8*], [5 x i8*]* @_ZTV9Rectangle, i32 0, i32 2")

    def test_const_other(self):
        result = get_value(["select", "i1", "true,", "i8", "17,", "i8", "42"])
        self.assertEqual(result[0], "select i1 true, i8 17, i8 42")

        result = get_value(["icmp", "eq", "i32", "4,", "5"])
        self.assertEqual(result[0], "icmp eq i32 4, 5")

        result = get_value(["fcmp", "oeq", "float", "4.0,", "5.0"])
        self.assertEqual(result[0], "fcmp oeq float 4.0, 5.0")

    def test_const_vector_op(self):
        result = get_value(["extractelement", "<2 x i32>", "<i32", "42,", "i32", "11>,", "i32", "0"])
        self.assertEqual(result[0], "extractelement <2 x i32> <i32 42, i32 11>, i32 0")

        result = get_value(["insertelement", "<2 x i32>", "<i32", "42,", "i32", "11>,", "i32", "1,", "i32", "0"])
        self.assertEqual(result[0], "insertelement <2 x i32> <i32 42, i32 11>, i32 1, i32 0")

        result = get_value(["shufflevector", "<2", "x", "i32>", "<i32", "42,", "i32", "11>,",
                            "<1", "x", "i32>", "<i32", "5>,",
                            "<3", "x", "i32>", "<i32", "0,", "i32", "2,", "i32", "1>"])
        self.assertEqual(result[0], "shufflevector <2 x i32> <i32 42, i32 11>, <1 x i32> <i32 5>, "
                                    "<3 x i32> <i32 0, i32 2, i32 1>")

    def test_const_aggregate_op(self):
        result = get_value(["extractvalue", "{i32,", "float}", "{i32", "4,", "float", "17.0},", "0"])
        self.assertEqual(result[0], "extractvalue {i32, float} {i32 4, float 17.0}, 0")

        result = get_value(["insertvalue", "{i32,", "float}", "{i32", "4,", "float", "17.0},", "i32", "4,", "0"])
        self.assertEqual(result[0], "insertvalue {i32, float} {i32 4, float 17.0}, i32 4, 0")

    def test_const_opcode(self):
        result = get_value(["add", "i32", "4,", "5"])
        self.assertEqual(result[0], "add i32 4, 5")

        result = get_value(["fadd", "float", "4.0,", "5.3"])
        self.assertEqual(result[0], "fadd float 4.0, 5.3")

        result = get_value(["sub", "nuw", "nsw", "i32", "4,", "2"])
        self.assertEqual(result[0], "sub nuw nsw i32 4, 2")

        result = get_value(["fsub", "nnan", "float", "4.0,", "2.2"])
        self.assertEqual(result[0], "fsub nnan float 4.0, 2.2")

        result = get_value(["mul", "nuw", "i32", "4,", "2"])
        self.assertEqual(result[0], "mul nuw i32 4, 2")

        result = get_value(["fmul", "nnan", "ninf", "float", "5.5,", "2.0"])
        self.assertEqual(result[0], "fmul nnan ninf float 5.5, 2.0")

        result = get_value(["udiv", "i32", "4,", "2"])
        self.assertEqual(result[0], "udiv i32 4, 2")

        result = get_value(["sdiv", "exact", "i32", "4,", "3"])
        self.assertEqual(result[0], "sdiv exact i32 4, 3")

        result = get_value(["fdiv", "float", "4.0,", "2.0"])
        self.assertEqual(result[0], "fdiv float 4.0, 2.0")

        result = get_value(["urem", "i32", "4,", "3"])
        self.assertEqual(result[0], "urem i32 4, 3")

        result = get_value(["srem", "i32", "4,", "3"])
        self.assertEqual(result[0], "srem i32 4, 3")

        result = get_value(["frem", "float", "4.0,", "3.0"])
        self.assertEqual(result[0], "frem float 4.0, 3.0")
