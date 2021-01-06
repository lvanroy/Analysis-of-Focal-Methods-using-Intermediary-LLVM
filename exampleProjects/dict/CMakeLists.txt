cmake_minimum_required(VERSION 3.10)
project(operations CXX)

function(target_link_libraries _target)
    set(_mode "PUBLIC")
    foreach(_arg IN LISTS ARGN)
        if (_arg MATCHES "INTERFACE|PUBLIC|PRIVATE|LINK_PRIVATE|LINK_PUBLIC|LINK_INTERFACE_LIBRARIES")
            set(_mode "${_arg}")
        else()
            if (NOT _arg MATCHES "debug|optimized|general")
                set_property(GLOBAL APPEND PROPERTY GlobalTargetDepends${_target} ${_arg})
            endif()
        endif()
    endforeach()
    _target_link_libraries(${_target} ${ARGN})
endfunction()

function(get_link_dependencies _target _listvar)
    set(_worklist ${${_listvar}})
    if (TARGET ${_target})
        list(APPEND _worklist ${_target})
        get_property(_dependencies GLOBAL PROPERTY GlobalTargetDepends${_target})
        foreach(_dependency IN LISTS _dependencies)
            if (NOT _dependency IN_LIST _worklist)
                get_link_dependencies(${_dependency} _worklist)
            endif()
        endforeach()
        set(${_listvar} "${_worklist}" PARENT_SCOPE)
    endif()
endfunction()

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
add_executable(test source/Dict.cpp test/test.cpp)
target_link_libraries(test gtest_main)

# emit source info
set(source_info "")
get_link_dependencies(test _deps)
foreach(_dep IN LISTS _deps)
    get_target_property(project_includes ${_dep} INCLUDE_DIRECTORIES)
    get_target_property(_srcs ${_dep} SOURCES)
    get_target_property(_src_dir ${_dep} SOURCE_DIR)
    set(source_info "${source_info}Includes:")
    foreach(include ${project_includes})
        set(source_info "${source_info}\n${include}")
    endforeach()
    set(source_info "${source_info}\nSources:")
    foreach(_src IN LISTS _srcs)
        set(source_info "${source_info}\n${_src_dir}/${_src}")
    endforeach()
    set(source_info "${source_info}\n\n")
endforeach()
FILE(WRITE ${CMAKE_BINARY_DIR}/projectconfig.txt ${source_info})
