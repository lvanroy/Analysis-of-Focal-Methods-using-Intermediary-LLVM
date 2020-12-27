from yaml import load
from os import path, getcwd
from shutil import which
from subprocess import call, DEVNULL
from argparse import ArgumentParser

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

config = load(open('config.yml').read(), Loader=Loader)

print("[1/4]: Validating environment - started")

if which("clang-6.0") is None:
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

if which("llvm-link-6.0") is None:
    print("Error: This tool requires llvm to operate, please install llvm and try again.")
    exit(0)
else:
    print("-- llvm found")


def create_build_dir(project_path):
    if not path.exists("{}/llvm".format(project_path)):
        call(["mkdir", "{}/llvm".format(project_path)], stdout=DEVNULL)

    if not path.exists("{}/llvm/llvm_submodules".format(project_path)):
        call(["mkdir", "{}/llvm/llvm_submodules".format(project_path)])


def build_project(project_path):
    c_compiler = "-DCMAKE_C_COMPILER={}".format(config["c"]["c_clang_path"])
    cxx_compiler = "-DCMAKE_CXX_COMPILER={}".format(config["c++"]["cxx_clang_path"])
    build_path = "{}/llvm".format(project_path)
    project_base = path.join(getcwd(), project_path)
    call(["cmake", c_compiler, cxx_compiler, project_base], cwd=build_path)

    phase = None
    includes = list()
    f = open("{}/projectconfig.txt".format(build_path), "r")

    for line in f.readlines():
        line = line.rstrip()

        if line == "Sources:":
            phase = "sources"
        elif line == "Includes:":
            includes = list()
            includes.append("-I")
            includes.append("/mnt/c/Users/larsv/Desktop/Goal-Oriented-Mutation-Testing/"
                            "exampleProjects/stride/main/cpp/geopop/io/proto_pb/")
            phase = "includes"
        elif line == "":
            continue
        elif phase == "includes":
            includes.append("-I")
            includes.append(line)
        elif phase == "sources":
            if line[-2:] == ".h":
                continue
            print("compiling: {}".format(line))
            if line[-2:] == ".c":
                call(["clang-6.0", "-S", "-emit-llvm", line] + includes,
                     cwd="{}/llvm_submodules".format(build_path))
            else:
                call(["clang++-6.0", "-std=c++17", "-S", "-emit-llvm", line] + includes,
                     cwd="{}/llvm_submodules".format(build_path))
            print("done")

    f.close()

    call(["llvm-link-6.0 *.ll -o linked.bc"], cwd="{}/llvm_submodules".format(build_path), shell=True)
    call(["llvm-dis-6.0", "./llvm_submodules/linked.bc", "-o", "linked.ll"], cwd=build_path)


parser = ArgumentParser(description='Compiler capable of compiling c++ project using cmake to LLVM IR.')
parser.add_argument('path', type=str, help='the path to the root cmake file')

args = parser.parse_args()

create_build_dir(args.path)
build_project(args.path)
