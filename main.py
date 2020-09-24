import os
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
    for root, dirs, files in os.walk(os.path.join("build")):
        for file in files:
            if file.startswith("{}.ll".format(config["test_executable"])):
                return os.path.join(os.getcwd(), os.path.join(root, file))
    return None


print("[1/4]: Validating environment - started")

if which("clang") is None:
    print("Error: This tool requires clang to operate, please install clang and try again.")
else:
    print("-- Cmake found")

if which("clang") is None:
    print("Error: This tool requires Cmake to operate, please install Cmake and try again.")
else:
    print("-- clang found")

if which("make") is None:
    print("Error: This tool requires make to operate, please install make and try again.")
else:
    print("-- make found")

print("[1/4]: Validating environment - finished")

print("[2/4]: building llvm - started")

call(["mkdir", "build"], stdout=DEVNULL)
print("-- cmake - started")
call(["CXX={}".format(config['c++']['cxx_clang_path'])], cwd="./build", shell=True)
call(["CC={}".format(config['c']['c_clang_path'])], cwd="./build", shell=True)
call(["cmake", "-DCMAKE_C_COMPILER={}".format(config['c']['c_clang_path']),
      "-DCMAKE_CXX_COMPILER={}".format(config['c++']['cxx_clang_path']),
      config['project_path']], cwd="./build")
print("-- cmake - finished")

print("-- make - started")
call(["cmake", "--build", ".", "--target", "llvm_dis"], cwd="./build")
print("-- make - finished")

print("[2/4]: building llvm - finished")
print("[3/4]: llvm analysis - started")
analyser = LLVMAnalyser()
analyser.analyse(determine_executable_path())
