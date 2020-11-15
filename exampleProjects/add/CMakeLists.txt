cmake_minimum_required(VERSION 3.10)
project(add CXX)

# import the LLVMIRutil cmake module
list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/../../cmake")
include(LLVMIRutil)

add_subdirectory(test)