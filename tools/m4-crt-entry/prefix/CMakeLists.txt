cmake_minimum_required(VERSION 3.24)
project(MW34CRTEntryFirstFault LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
get_filename_component(MW34_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../../.." ABSOLUTE)
add_executable(mw34_crt_entry_first_fault "${MW34_PREFIX_SOURCE}" "${MW34_ROOT}/tools/m4-crt/crt_services.cpp"
 "${MW34_ROOT}/tools/m4-runtime/runtime.cpp"
 "${MW34_ROOT}/tools/m4-startup/image_loader.cpp"
 "${MW34_ROOT}/runtime/memory/guest_memory.cpp" "${MW34_ENTRY_OBJECT}")
target_include_directories(mw34_crt_entry_first_fault PRIVATE "${MW34_ROOT}/tools/m4-crt" "${MW34_ROOT}/tools/m4-runtime" "${MW34_ROOT}/tools/m4-startup" "${MW34_ROOT}/runtime")
target_include_directories(mw34_crt_entry_first_fault SYSTEM PRIVATE "${MW34_ROOT}/local/tools/remill-v6.0.1/remill-6.0.1/include")
target_compile_definitions(mw34_crt_entry_first_fault PRIVATE ADDRESS_SIZE_BITS=32 HAS_FEATURE_AVX=0 HAS_FEATURE_AVX512=0)
target_compile_options(mw34_crt_entry_first_fault PRIVATE /W4 /WX /permissive- /showIncludes)
target_link_libraries(mw34_crt_entry_first_fault PRIVATE bcrypt)
