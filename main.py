from shutil import which
from yaml import load

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

from llvmAnalyser.analyser import LLVMAnalyser

with open('config.yml', 'r') as f:
    config = load(f.read(), Loader=Loader)

print("[1/3]: Validating environment - started")

if which("dot") is None:
    print("Error: This tool requires graphviz to operate, please install graphviz and try again.")
    exit(0)
else:
    print("-- graphviz found")

print("[1/3]: Validating environment - finished")

print("[2/3]: llvm analysis - started")

llvm_path = config["project_path"] + "/llvm/linked.ll"
analyzer = LLVMAnalyser()
analyzer.get_relevant_functions(llvm_path)

print("[2/3]: llvm analysis - finished")
print("[3/3]: focal method analysis - started")

focal_methods = analyzer.get_focal_methods()

print("[3/3]: focal method analysis - finished")
