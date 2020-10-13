from os import path, walk, getcwd
from shutil import which
from subprocess import call, DEVNULL
from yaml import load

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

from llvmAnalyser.analyser import LLVMAnalyser

config = load(open('config.yml').read(), Loader=Loader)


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

if which("clang") is None:
    print("Error: This tool requires clang to operate, please install clang and try again.")
    exit(0)
else:
    print("-- clang found")

if which("cmake") is None:
    print("Error: This tool requires Cmake to operate, please install Cmake and try again.")
    exit(0)
else:
    print("-- Cmake found")

if which("make") is None:
    print("Error: This tool requires make to operate, please install make and try again.")
    exit(0)
else:
    print("-- make found")

if which("dot") is None:
    print("Error: This tool requires graphviz to operate, please install graphviz and try again.")
    exit(0)
else:
    print("-- graphviz found")

if which("llvm-link") is None:
    print("Error: This tool requires llvm to operate, please install llvm and try again.")
    exit(0)
else:
    print("-- llvm found")

print("[1/4]: Validating environment - finished")

print("[2/4]: building llvm - started")

if not path.exists("build"):
    call(["mkdir", "build"], stdout=DEVNULL)

print("-- cmake - started")
call(["CXX={}".format(config['c++']['cxx_clang_path'])], cwd="./build", shell=True)
call(["CC={}".format(config['c']['c_clang_path'])], cwd="./build", shell=True)
call(["cmake", "-DCMAKE_C_COMPILER={}".format(config['c']['c_clang_path']),
      "-DCMAKE_CXX_COMPILER={}".format(config['c++']['cxx_clang_path']),
      config['project_path']], cwd="./build")
print("-- cmake - finished")

print("-- make - started")
call(["cmake", "--build", ".", "--target", config["build_target"]], cwd="./build")
print("-- make - finished")

libs = get_libs(config["c++"]["test_framework"])
arguments = ["llvm-link", determine_executable_path()]
for lib in libs:
    arguments.append(lib)
arguments += ["-o", "link.bc"]
call(arguments, cwd="./build")
call(["llvm-dis", "link.bc", "-o", "link_ir.ll"], cwd="./build")

print("[2/4]: building llvm - finished")
print("[3/4]: llvm analysis - started")
analyser = LLVMAnalyser()
analyser.analyse("./build/link_ir.ll")
print("[3/4]: llvm analysis - finished")
