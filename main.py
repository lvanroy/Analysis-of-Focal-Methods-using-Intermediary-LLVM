from os import path, walk, getcwd
from shutil import which
from subprocess import call, DEVNULL
from yaml import load

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

from llvmAnalyser.analyser import LLVMAnalyser

with open('config.yml', 'r') as f:
    config = load(f.read(), Loader=Loader)


def determine_executable_path():
    for root, dirs, files in walk(path.join("build")):
        for file in files:
            if file.startswith("test_link.ll"):
                return path.join(getcwd(), path.join(root, file))
    return ""


def get_libs(testing_framework):
    if testing_framework == "gtest":
        return ["../testing_frameworks/gtest/gtest_main.ll"]


print("[1/4]: Validating environment - started")

if which("dot") is None:
    print("Error: This tool requires graphviz to operate, please install graphviz and try again.")
    exit(0)
else:
    print("-- graphviz found")

print("[1/4]: Validating environment - finished")

print("[2/4]: building llvm - started")

if not path.exists("build"):
    call(["mkdir", "build"], stdout=DEVNULL)

print("-- cmake - started")
c_compiler = "-DCMAKE_C_COMPILER={}".format(config["c"]["c_clang_path"])
cxx_compiler = "-DCMAKE_CXX_COMPILER={}".format(config["c++"]["cxx_clang_path"])
call(["cmake", c_compiler, cxx_compiler, config['project_path']], cwd="./build")
print("-- cmake - finished")

print("-- make - started")
call(["cmake", "--build", ".", "--target", config["build_target"]], cwd="./build")
print("-- make - finished")

libs = get_libs(config["test_framework"])
arguments = ["llvm-link", determine_executable_path()]
arguments += libs
arguments += ["-o", "link.bc"]
call(arguments, cwd="./build")
call(["llvm-dis", "link.bc", "-o", "link_ir.ll"], cwd="./build")

print("[2/4]: building llvm - finished")
print("[3/4]: llvm analysis - started")
analyser = LLVMAnalyser()
analyser.analyse("./build/link_ir.ll")
print("[3/4]: llvm analysis - finished")
