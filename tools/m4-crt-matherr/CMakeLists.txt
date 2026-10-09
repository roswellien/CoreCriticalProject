cmake_minimum_required(VERSION 3.24)
project(MW34MatherrNative LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
get_filename_component(WORKSPACE "${CMAKE_CURRENT_SOURCE_DIR}/../.." ABSOLUTE)
if(NOT MW34_MATHERR_OBJECT)
 message(FATAL_ERROR "Private complete source-lowered object required")
endif()
add_executable(mw34_matherr_native native.cpp "${MW34_MATHERR_OBJECT}"
 "${WORKSPACE}/tools/m4-runtime/runtime.cpp" "${WORKSPACE}/tools/m4-startup/image_loader.cpp"
 "${WORKSPACE}/runtime/memory/guest_memory.cpp")
target_include_directories(mw34_matherr_native PRIVATE "${WORKSPACE}/tools/m4-runtime"
 "${WORKSPACE}/tools/m4-startup" "${WORKSPACE}/runtime")
target_include_directories(mw34_matherr_native SYSTEM PRIVATE
 "${WORKSPACE}/local/tools/remill-v6.0.1/remill-6.0.1/include")
target_compile_definitions(mw34_matherr_native PRIVATE ADDRESS_SIZE_BITS=32 HAS_FEATURE_AVX=0 HAS_FEATURE_AVX512=0)
target_compile_options(mw34_matherr_native PRIVATE /W4 /WX /permissive-)
target_link_libraries(mw34_matherr_native PRIVATE bcrypt)
