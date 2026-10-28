# The historical research-object build remains below the opt-in branch in CMakeLists.txt.
if(NOT WIN32 OR NOT CMAKE_SIZEOF_VOID_P EQUAL 8)
    message(FATAL_ERROR "The native host requires Windows x64")
endif()
if(NOT CMAKE_CXX_COMPILER_ID MATCHES "Clang")
    message(FATAL_ERROR "Use the pinned clang-cl compiler; the host uses Clang inline assembly")
endif()
foreach(required MW34_REMILL_INCLUDE MW34_VULKAN_INCLUDE MW34_TRANSLATED_LIBRARY MW34_HOST_DEFINITION MW34_GAME_DIRECTORY)
    if(NOT DEFINED ${required})
        message(FATAL_ERROR "Missing ${required}; use build_host.ps1")
    endif()
endforeach()
get_filename_component(MW34_ROOT "${CMAKE_CURRENT_LIST_DIR}/../../.." ABSOLUTE)
set(host "${CMAKE_CURRENT_LIST_DIR}/../host")
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
string(REPLACE "/EHsc" "" CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS}")
add_executable(entry_commandline
    "${host}/composition.cpp"
    "${host}/crt_services.cpp"
    "${host}/guest_memory_cached.cpp"
    "${MW34_ROOT}/tools/m4-guest-cw/guest_cw.cpp"
    "${MW34_ROOT}/tools/m4-crt-fdiv/registry.cpp"
    "${MW34_ROOT}/tools/m4-runtime/runtime.cpp"
    "${MW34_ROOT}/tools/m4-startup/image_loader.cpp")
target_include_directories(entry_commandline BEFORE PRIVATE
    "${host}" "${CMAKE_CURRENT_LIST_DIR}/.."
    "${MW34_ROOT}/tools/m4-crt" "${MW34_ROOT}/tools/m4-crt-fdiv"
    "${MW34_ROOT}/tools/m4-crt-commandline-native" "${MW34_ROOT}/tools/m4-runtime"
    "${MW34_ROOT}/tools/m4-startup" "${MW34_ROOT}/tools/m4-guest-cw"
    "${MW34_ROOT}/runtime")
target_include_directories(entry_commandline SYSTEM PRIVATE
    "${MW34_REMILL_INCLUDE}" "${MW34_VULKAN_INCLUDE}")
target_compile_definitions(entry_commandline PRIVATE
    ADDRESS_SIZE_BITS=32 HAS_FEATURE_AVX=0 HAS_FEATURE_AVX512=0
    MW34_ENTRY_OBJECT_SHA="377920315f123783d799400c1d3df4392d09b1c6de9cb7079f2ad7f253f1fea8"
    MW34_CONTROL_OBJECT_SHA="8851974290bd5a86589d3a8135190e3b916659f31534288a01ded60152d90471"
    MW34_INITTERM_SOURCE_SHA="960ed0d00b0200736930590a16fbb3caa9c3bc24af9851a3728258fd9b340678"
    MW34_MAINARGS_RECOVERY_SHA="ea623fb2d4bbad3e7636e8155eaafbc6ce6915e293fdd851e4f9eadbc2e0c038"
    MW34_REPLAY_INPUT_SHA="4294b8d926966c04d305b6e22a9166f08a328f4cc1c62984b72677fe83dd638a"
    MW34_MFC42_PATH="${MW34_GAME_DIRECTORY}/MFC42.DLL"
    MW34_MSVCP50_PATH="${MW34_GAME_DIRECTORY}/MSVCP50.DLL")
target_compile_options(entry_commandline PRIVATE /EHs /O2 /Ob2)
target_link_libraries(entry_commandline PRIVATE
    "${MW34_TRANSLATED_LIBRARY}" bcrypt dxguid version winmm vfw32)
target_link_options(entry_commandline PRIVATE
    "/DEF:${MW34_HOST_DEFINITION}" /INCREMENTAL:NO /SUBSYSTEM:CONSOLE /OPT:REF /OPT:ICF)
