cmake_minimum_required(VERSION 3.10)

project(add_int CXX)

list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/../cmake")

include(LLVMIRutil)

set(SOURCES source/add.cpp source/main.cpp)

add_executable(add_int ${SOURCES})

# specify linker language, required by llvmir cmake
# set_target_properties(add_int PROPERTIES LINKER_LANGUAGE CXX)

# create llvm target
# llvmir_attach_bc_target(add_int_bc add_int)
# add_dependencies(add_int_bc add_int)

# create pass target
# llvmir_attach_opt_pass_target(add_int_pass1 add_int_bc -mem2reg)
# add_dependencies(add_int_pass1 add_int_bc)

# llvmir_attach_opt_pass_target(add_int_pass2 add_int_pass1 -simplifycfg -licm)
# add_dependencies(add_int_pass2 add_int_pass1)

# create llvm link target
# llvmir_attach_link_target(add_int_link add_int_pass2)
# add_dependencies(add_int_link add_int_pass2)

# create llvm disassemble target
# llvmir_attach_disassemble_target(add_int_dis add_int_link)
# add_dependencies(add_int_dis add_int_link)

add_subdirectory(test)
