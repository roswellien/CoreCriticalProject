cmake_minimum_required(VERSION 3.24)
project(MW34OwnCRTEntryFirstFault LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
string(REPLACE "/EHsc" "" CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS}")
get_filename_component(WORKSPACE "${CMAKE_CURRENT_SOURCE_DIR}/../.." ABSOLUTE)
add_executable(controls controls.cpp "${MW34_GUEST_OBJECT}"
 "${WORKSPACE}/tools/m4-crt/crt_services.cpp"
 "${WORKSPACE}/tools/m4-runtime/runtime.cpp"
 "${WORKSPACE}/tools/m4-startup/image_loader.cpp"
 "${WORKSPACE}/runtime/memory/guest_memory.cpp")
target_include_directories(controls PRIVATE "${WORKSPACE}/tools/m4-crt" "${WORKSPACE}/tools/m4-runtime" "${WORKSPACE}/tools/m4-startup" "${WORKSPACE}/runtime")
target_include_directories(controls SYSTEM PRIVATE "${WORKSPACE}/local/tools/remill-v6.0.1/remill-6.0.1/include")
target_compile_definitions(controls PRIVATE ADDRESS_SIZE_BITS=32 HAS_FEATURE_AVX=0 HAS_FEATURE_AVX512=0)
target_compile_options(controls PRIVATE /W4 /WX /EHs /permissive-)
target_link_libraries(controls PRIVATE bcrypt)
