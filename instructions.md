There is a script provided to convert C++ projects to LLVM IR. The only requirement for this script to work is that the C++ project uses cmake and that the following configuration is present within this file. The following two functions need to be defined at the start of the cmake to override existing functions within CMake so that all dependencies are tracked.

```
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
```

Using this configuration, we will now need to output a file documenting these depencies so that we can link the llvm files, the following configuration needs to be added at the end of the cmake file to do so.

```
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
```

Using this configuration the provided CompileC++ script will generate a fully merged LLVM IR file.

Both the compileC++ script as well as the entire compilation take their imput from the config.yml fail that is also provided within the root directory. This configuration includes the root directory of the project in which the CMake file resides, the three regexes that are required by the tool, the maximal depth and whether or not we want the tool to output the graph it generated for manual debugging of the results. The test_function_signature regex is used to identify the test functions, the assert_function signature is used to identify the assertions and the exclusion_filter will be used to identify functions which should not be considered as being functions under test. All three of these regexes will be applied to LLVM IR code and should therefore be conformant with the name signatures that are used within LLVM IR. The names used by LLVM are mangled and will contain a combination of the namespace, the function name and the arguments (which are all preserved) so if a certain naming convention would have worked in the original source code, it should also work within LLVM IR.

To perform actual analysis on this LLVM IR file that is generated, we simply need to invoke the main script (given that the LLVM IR is generated). No additional arguments are needed, as the C++ compile script will have generated the LLVM IR within the directory of the project.

If any other programming languages are desired, the only component that will need to be added is the compilation script, once the LLVM IR is generated there is no langauge dependent component left, and the tool can directly analyse the result.
