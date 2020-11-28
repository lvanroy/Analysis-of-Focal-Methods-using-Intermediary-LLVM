cmake_minimum_required(VERSION 3.10)
project(add CXX)

# import the LLVMIRutil cmake code
list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/../../cmake")
include(LLVMIRutil)

# Download and unpack googletest at configure time
configure_file(CMakeLists.txt.in googletest-download/CMakeLists.txt)
execute_process(COMMAND ${CMAKE_COMMAND} -G "${CMAKE_GENERATOR}" .
        RESULT_VARIABLE result
        WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/googletest-download )
if(result)
    message(FATAL_ERROR "CMake step for googletest failed: ${result}")
endif()
execute_process(COMMAND ${CMAKE_COMMAND} --build .
        RESULT_VARIABLE result
        WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/googletest-download )
if(result)
    message(FATAL_ERROR "Build step for googletest failed: ${result}")
endif()

# Prevent overriding the parent project's compiler/linker
# settings on Windows
set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)

# Add googletest directly to our build. This defines
# the gtest and gtest_main targets.
add_subdirectory(${CMAKE_CURRENT_BINARY_DIR}/googletest-src
        ${CMAKE_CURRENT_BINARY_DIR}/googletest-build
        EXCLUDE_FROM_ALL)

# The gtest/gtest_main targets carry header search path
# dependencies automatically when using CMake 2.8.11 or
# later. Otherwise we have to add them here ourselves.
if (CMAKE_VERSION VERSION_LESS 2.8.11)
    include_directories("${gtest_SOURCE_DIR}/include")
endif()

# Now simply link against gtest or gtest_main as needed.
include_directories(${CMAKE_CURRENT_BINARY_DIR}/googletest-src/googletest/include)
include_directories(${CMAKE_SOURCE_DIR}/source)
add_executable(test test/test.cpp source/add.cpp)
target_link_libraries(test gtest_main)

# specify linker language, required by llvmir cmake
set_target_properties(test PROPERTIES LINKER_LANGUAGE CXX)
set_target_properties(test PROPERTIES INTERPROCEDURAL_OPTIMIZATION TRUE)

# target_compile_options(test PUBLIC ${CMAKE_CXX_FLAGS} -flto)

# create llvm target
llvmir_attach_bc_target(test_bc test)
add_dependencies(test_bc test)

# create llvm link target
llvmir_attach_link_target(test_link test_bc)
add_dependencies(test_link test_bc)

# create llvm disassemble target
llvmir_attach_disassemble_target(llvm_dis test_link)
add_dependencies(llvm_dis test_link)
