import unittest
from llvmAnalyser.types import *


class TestLLVMTypes(unittest.TestCase):
    def test_array_type(self):
        self.assertEqual(get_array_type(["[4", "x", "i32]"])[0], "[4 x i32]")
        self.assertEqual(get_array_type(["[8", "x", "[4", "x", "float]]", "test"])[0], "[8 x [4 x float]]")
        self.assertEqual(get_array_type(["[2", "x", "[3", "x", "[4", "x", "i16]]]"])[0], "[2 x [3 x [4 x i16]]]")
        self.assertEqual(get_array_type(["{i32", "i32}"]), None)
        self.assertEqual(get_array_type(["<{i8,", "i32}>"]), None)
        self.assertEqual(get_array_type(["<4", "x", "i64*>"]), None)

    def test_struct_type(self):
        self.assertEqual(get_struct_type(["{i32,", "i32,", "i32}"])[0], "{i32, i32, i32}")
        self.assertEqual(get_struct_type(["{float,", "i32,", "(i32)", "*}", "test"])[0], "{float, i32, (i32) *}")
        self.assertEqual(get_struct_type(["<{i8,", "i32}>"])[0], "<{i8, i32}>")
        self.assertEqual(get_struct_type(['{', '%"struct.std::_Rb_tree_node_base"*,', 'i8', '}'])[0],
                         '{ %"struct.std::_Rb_tree_node_base"*, i8 }')
        self.assertEqual(get_struct_type(["[4", "x", "i32]"]), None)
        self.assertEqual(get_struct_type(["<4", "x", "i64*>"]), None)

    def test_vector_type(self):
        self.assertEqual(get_vector_type(["<4", "x", "i32>"])[0], "<4 x i32>")
        self.assertEqual(get_vector_type(["<8", "x", "float>"])[0], "<8 x float>")
        self.assertEqual(get_vector_type(["<2", "x", "i64>", "test"])[0], "<2 x i64>")
        self.assertEqual(get_vector_type(["<4", "x", "i64*>"])[0], "<4 x i64*>")
        self.assertEqual(get_vector_type(["<vscale", "x", "4", "x", "i32>"])[0], "<vscale x 4 x i32>")
        self.assertEqual(get_vector_type(["{i32", "i32}"]), None)
        self.assertEqual(get_vector_type(["<{i8,", "i32}>"]), None)
        self.assertEqual(get_vector_type(["[4", "x", "i32]"]), None)

    def test_pointer_type(self):
        self.assertEqual(get_array_type(["[4", "x", "i32]*"])[0], "[4 x i32]*")
        self.assertEqual(get_array_type(["[8", "x", "[4", "x", "float]]", "*"])[0], "[8 x [4 x float]] *")
        self.assertEqual(get_struct_type(["{float,", "i32,", "(i32)", "*}", "*"])[0], "{float, i32, (i32) *} *")
        self.assertEqual(get_struct_type(["<{i8,", "i32}>*", "test"])[0], "<{i8, i32}>*")
        self.assertEqual(get_vector_type(["<2", "x", "i64>", "*"])[0], "<2 x i64> *")
        self.assertEqual(get_vector_type(["<4", "x", "i64*>*"])[0], "<4 x i64*>*")
        self.assertEqual(check_for_pointer_type("void", ["*,", "i8"])[0], "void *")
        self.assertEqual(check_for_pointer_type("void", ["*,", "i8"])[1], ["i8"])
        self.assertEqual(get_vector_type(["{i32", "i32}*"]), None)
        self.assertEqual(get_vector_type(["<{i8,", "i32}>", "*"]), None)
        self.assertEqual(get_vector_type(["[4", "x", "i32]*"]), None)
        self.assertEqual(get_struct_type(["[4", "x", "i32]*"]), None)
        self.assertEqual(get_struct_type(["<4", "x", "i64*>", "*"]), None)
        self.assertEqual(get_array_type(["{i32", "i32}*"]), None)
        self.assertEqual(get_array_type(["<{i8,", "i32}>", "*"]), None)
        self.assertEqual(get_array_type(["<4", "x", "i64*>*"]), None)
        self.assertEqual(get_array_type(["void", "a(i32*", "i8)"][0]), None)
        result = get_type(['%"class.testing::Message"*', '(%"class.std::basic_ostream"*)*)', '#3',
                           'comdat', 'align', '2', '{'])
        self.assertEqual(result[0], '%"class.testing::Message"* (%"class.std::basic_ostream"*)*')
        self.assertEqual(result[1], ['#3', 'comdat', 'align', '2', '{'])

    def test_function_type(self):
        self.assertEqual(get_vector_type(["<4", "x", "i32>(i32)"])[0], "<4 x i32>(i32)")
        self.assertEqual(get_vector_type(["<2", "x", "i64>", "*(i32,", "i32)"])[0], "<2 x i64> *(i32, i32)")
        self.assertEqual(get_struct_type(["{float,", "i32,", "(i32)", "*}", "(i1)"])[0], "{float, i32, (i32) *} (i1)")
        self.assertEqual(get_struct_type(["<{i8,", "i32}>()"])[0], "<{i8, i32}>()")
        self.assertEqual(get_array_type(["[4", "x", "i32]", "(...)", "test"])[0], "[4 x i32] (...)")
        self.assertEqual(get_array_type(["[8", "x", "[4", "x", "float]](i8,", "float)"])[0],
                         "[8 x [4 x float]](i8, float)")
        self.assertEqual(get_type(['void',
                                   '(%"class.std::basic_ifstream.4806"*,',
                                   '%"class.std::__cxx11::basic_string"*,',
                                   'i32)*'])[0],
                         'void (%"class.std::basic_ifstream.4806"*, %"class.std::__cxx11::basic_string"*, i32)*')
        self.assertEqual(get_vector_type(["{i32", "i32}*()"]), None)
        self.assertEqual(get_vector_type(["<{i8,", "i32}>", "*", "(...)"]), None)
        self.assertEqual(get_vector_type(["[4", "x", "i32]*(i8)"]), None)
        self.assertEqual(get_struct_type(["[4", "x", "i32]*", "(i1)"]), None)
        self.assertEqual(get_struct_type(["<4", "x", "i64*>", "*", "(i8,", "float)"]), None)
        self.assertEqual(get_array_type(["{i32", "i32}*", "(i8)"]), None)
        self.assertEqual(get_array_type(["<{i8,", "i32}>", "*(...)"]), None)
        self.assertEqual(get_array_type(["<4", "x", "i64*>*()"]), None)

    def test_general_type_function(self):
        self.assertEqual(get_type(["[4", "x", "i32]"])[0], "[4 x i32]")
        self.assertEqual(get_type(["[8", "x", "[4", "x", "float]]", "test"])[0], "[8 x [4 x float]]")
        self.assertEqual(get_type(["[2", "x", "[3", "x", "[4", "x", "i16]]]"])[0], "[2 x [3 x [4 x i16]]]")
        self.assertEqual(get_type(["{i32,", "i32,", "i32}"])[0], "{i32, i32, i32}")
        self.assertEqual(get_type(["{float,", "i32,", "(i32)", "*}", "test"])[0], "{float, i32, (i32) *}")
        self.assertEqual(get_type(["<{i8,", "i32}>"])[0], "<{i8, i32}>")
        self.assertEqual(get_type(["<4", "x", "i32>"])[0], "<4 x i32>")
        self.assertEqual(get_type(["<8", "x", "float>"])[0], "<8 x float>")
        self.assertEqual(get_type(["<2", "x", "i64>", "test"])[0], "<2 x i64>")
        self.assertEqual(get_type(["<4", "x", "i64*>"])[0], "<4 x i64*>")
        self.assertEqual(get_type(["<vscale", "x", "4", "x", "i32>"])[0], "<vscale x 4 x i32>")
        self.assertEqual(get_type(["[4", "x", "i32]*"])[0], "[4 x i32]*")
        self.assertEqual(get_type(["[8", "x", "[4", "x", "float]]", "*"])[0], "[8 x [4 x float]] *")
        self.assertEqual(get_type(["{float,", "i32,", "(i32)", "*}", "*"])[0], "{float, i32, (i32) *} *")
        self.assertEqual(get_type(["<{i8,", "i32}>*", "test"])[0], "<{i8, i32}>*")
        self.assertEqual(get_type(["<2", "x", "i64>", "*"])[0], "<2 x i64> *")
        self.assertEqual(get_type(["<4", "x", "i64*>*"])[0], "<4 x i64*>*")
        self.assertEqual(get_type(["<4", "x", "i32>(i32)"])[0], "<4 x i32>(i32)")
        self.assertEqual(get_type(["<2", "x", "i64>", "*(i32,", "i32)"])[0], "<2 x i64> *(i32, i32)")
        self.assertEqual(get_type(["{float,", "i32,", "(i32)", "*}", "(i1)"])[0], "{float, i32, (i32) *} (i1)")
        self.assertEqual(get_type(["<{i8,", "i32}>()"])[0], "<{i8, i32}>()")
        self.assertEqual(get_type(["[4", "x", "i32]", "(...)", "test"])[0], "[4 x i32] (...)")
        self.assertEqual(get_type(["[8", "x", "[4", "x", "float]](i8,", "float)"])[0], "[8 x [4 x float]](i8, float)")
        self.assertEqual(get_type(["i32"])[0], "i32")
        self.assertEqual(get_type(["void"])[0], "void")
        self.assertEqual(get_type(["void)"])[0], "void")
        self.assertEqual(get_type(["void", "(%test)*"])[0], "void (%test)*")
        self.assertEqual(get_type(["half", "test"])[0], "half")
        self.assertEqual(get_type(["@test<i32>"])[0], "@test<i32>")
        self.assertEqual(get_type(["@test<4", "x", "6>"])[0], "@test<4 x 6>")
