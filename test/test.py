import unittest

from os import path, getcwd
from subprocess import call, DEVNULL
from yaml import load
from llvmAnalyser.analyser import LLVMAnalyser

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

config = load(open('config.yml').read(), Loader=Loader)


def create_build_dir(project_path):
    if not path.exists("{}/build".format(project_path)):
        call(["mkdir", "{}/build".format(project_path)], stdout=DEVNULL)


def build_project(project_path):
    c_compiler = "-DCMAKE_C_COMPILER={}".format(config["c"]["c_clang_path"])
    cxx_compiler = "-DCMAKE_CXX_COMPILER={}".format(config["c++"]["cxx_clang_path"])
    build_path = "{}/build".format(project_path)
    project_base = path.join(getcwd(), project_path)
    call(["cmake", c_compiler, cxx_compiler, project_base], cwd=build_path, stdout=DEVNULL)

    call(["cmake", "--build", ".", "--target", "llvm_dis"], cwd=build_path)

    test_executable_path = "llvm-ir/llvm_dis/test_link.ll".format(build_path)
    gtest_main = path.join(getcwd(), "testing_frameworks/gtest/gtest_main.ll")
    call(["llvm-link", test_executable_path, gtest_main, "-o", "link.bc"], cwd=build_path)
    call(["llvm-dis", "link.bc", "-o", "link_ir.ll"], cwd=build_path)


def analyze_function(project_path):
    analyzer = LLVMAnalyser()
    analyzer.config["graph"] = False

    return analyzer.analyse("{}/build/link_ir.ll".format(project_path))


class TestTool(unittest.TestCase):
    def test_add(self):
        project_path = "exampleProjects/add"
        create_build_dir(project_path)
        build_project(project_path)
        focal_methods = analyze_function(project_path)

        self.assertEqual(focal_methods['@_ZN15ADDTEST_eq_Test8TestBodyEv'].pop(), '@_Z7add_intii')
        self.assertEqual(len(focal_methods['@_ZN15ADDTEST_eq_Test8TestBodyEv']), 0)

        self.assertEqual(focal_methods['@_ZN16ADDTEST_neq_Test8TestBodyEv'].pop(), '@_Z7add_intii')
        self.assertEqual(len(focal_methods['@_ZN16ADDTEST_neq_Test8TestBodyEv']), 0)

    # def test_operations(self):
    #     project_path = "exampleProjects/operations"
    #     create_build_dir(project_path)
    #     build_project(project_path)
    #     focal_methods = analyze_function(project_path)
    #
    #     for focal_method in focal_methods:
    #         print("self.assertEqual(focal_methods['{}'].pop(), '{}')".format(focal_method, focal_methods[focal_method].pop()))
    #
    #     self.assertEqual(focal_methods[' @_ZN22OPERATIONTEST_add_Test8TestBodyEv'].pop(), '@_ZN10Operations3addEii')
    #     self.assertEqual(len(focal_methods[' @_ZN22OPERATIONTEST_add_Test8TestBodyEv']), 0)
    #
    #     self.assertEqual(focal_methods['@_ZN15ADDTEST_eq_Test8TestBodyEv'].pop(), '@_Z7add_intii')
    #     self.assertEqual(len(focal_methods['@_ZN15ADDTEST_eq_Test8TestBodyEv']), 0)
    #
    #     self.assertEqual(focal_methods['@_ZN15ADDTEST_eq_Test8TestBodyEv'].pop(), '@_Z7add_intii')
    #     self.assertEqual(len(focal_methods['@_ZN15ADDTEST_eq_Test8TestBodyEv']), 0)
    #
    #     self.assertEqual(focal_methods['@_ZN15ADDTEST_eq_Test8TestBodyEv'].pop(), '@_Z7add_intii')
    #     self.assertEqual(len(focal_methods['@_ZN15ADDTEST_eq_Test8TestBodyEv']), 0)
    #
    #     self.assertEqual(focal_methods['@_ZN15ADDTEST_eq_Test8TestBodyEv'].pop(), '@_Z7add_intii')
    #     self.assertEqual(len(focal_methods['@_ZN15ADDTEST_eq_Test8TestBodyEv']), 0)
    #
    #     self.assertEqual(focal_methods['@_ZN15ADDTEST_eq_Test8TestBodyEv'].pop(), '@_Z7add_intii')
    #     self.assertEqual(len(focal_methods['@_ZN15ADDTEST_eq_Test8TestBodyEv']), 0)
    #
    #     self.assertEqual(focal_methods['@_ZN15ADDTEST_eq_Test8TestBodyEv'].pop(), '@_Z7add_intii')
    #     self.assertEqual(len(focal_methods['@_ZN15ADDTEST_eq_Test8TestBodyEv']), 0)
    #
    #     self.assertEqual(focal_methods['@_ZN15ADDTEST_eq_Test8TestBodyEv'].pop(), '@_Z7add_intii')
    #     self.assertEqual(len(focal_methods['@_ZN15ADDTEST_eq_Test8TestBodyEv']), 0)
    #
    #     self.assertEqual(focal_methods['@_ZN15ADDTEST_eq_Test8TestBodyEv'].pop(), '@_Z7add_intii')
    #     self.assertEqual(len(focal_methods['@_ZN15ADDTEST_eq_Test8TestBodyEv']), 0)
    #
    #     self.assertEqual(focal_methods['@_ZN15ADDTEST_eq_Test8TestBodyEv'].pop(), '@_Z7add_intii')
    #     self.assertEqual(len(focal_methods['@_ZN15ADDTEST_eq_Test8TestBodyEv']), 0)
    #
    #     self.assertEqual(focal_methods['@_ZN15ADDTEST_eq_Test8TestBodyEv'].pop(), '@_Z7add_intii')
    #     self.assertEqual(len(focal_methods['@_ZN15ADDTEST_eq_Test8TestBodyEv']), 0)
    #
    #     self.assertEqual(focal_methods['@_ZN15ADDTEST_eq_Test8TestBodyEv'].pop(), '@_Z7add_intii')
    #     self.assertEqual(len(focal_methods['@_ZN15ADDTEST_eq_Test8TestBodyEv']), 0)

    # def test_simple_class(self):
    #     project_path = "exampleProjects/simple_class"
    #     create_build_dir(project_path)
    #     build_project(project_path)
    #
    #     analyze_function(project_path)
