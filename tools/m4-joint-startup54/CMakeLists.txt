cmake_minimum_required(VERSION 3.24)
project(MW34JointStartup54 LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
string(REPLACE "/EHsc" "" CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS}")
if(NOT MW34_ROOT OR NOT MW34_PREP OR NOT MW34_LEVEL OR NOT MW34_OBJECTS OR NOT MW34_WRITER OR NOT MW34_REGISTRY OR NOT MW34_REGISTRY_INCLUDE)
 message(FATAL_ERROR "Exact frozen preparation/registry/level/literal objects/canonical writer required")
endif()
file(GLOB MW34_FP_CPP "${MW34_PREP}/derived/*.cpp")
add_executable(mw34_joint_startup54 "${MW34_PREP}/native_main.cpp" ${MW34_FP_CPP}
 "${MW34_PREP}/derived/chain/runtime_adapter.cpp" "${MW34_PREP}/derived/integer/runtime_adapter.cpp"
 "${MW34_PREP}/chain_dispatch.cpp" "${MW34_ROOT}/tools/m4-integer-startup/component.cpp" "${MW34_REGISTRY}"
 "${MW34_REGISTRY_INCLUDE}/crt_services.cpp" "${MW34_ROOT}/tools/m4-guest-cw/guest_cw.cpp"
 "${MW34_ROOT}/tools/m4-runtime/runtime.cpp" "${MW34_ROOT}/tools/m4-startup/image_loader.cpp"
 "${MW34_ROOT}/runtime/memory/guest_memory.cpp" ${MW34_OBJECTS} "${MW34_WRITER}" "${MW34_ROOT}/reports/m4-capture-direct/build-r4/preserve.obj")
target_include_directories(mw34_joint_startup54 PRIVATE "${MW34_PREP}" "${MW34_PREP}/${MW34_LEVEL}" "${MW34_REGISTRY_INCLUDE}" "${MW34_REGISTRY_INCLUDE}/${MW34_LEVEL}"
 "${MW34_ROOT}/tools/m4-runtime" "${MW34_ROOT}/tools/m4-startup" "${MW34_ROOT}/runtime" "${MW34_ROOT}/tools/m4-fp-numeric-max"
 "${MW34_ROOT}/tools/m4-crt" "${MW34_ROOT}/tools/m4-crt-fdiv" "${MW34_ROOT}/tools/m4-crt-commandline-native" "${MW34_ROOT}/tools/m4-guest-cw")
target_include_directories(mw34_joint_startup54 SYSTEM PRIVATE "${MW34_ROOT}/local/tools/remill-v6.0.1/remill-6.0.1/include")
target_compile_definitions(mw34_joint_startup54 PRIVATE ADDRESS_SIZE_BITS=32 HAS_FEATURE_AVX=0 HAS_FEATURE_AVX512=0)
target_compile_options(mw34_joint_startup54 PRIVATE /EHs /clang:-frounding-math)
set_source_files_properties("${MW34_REGISTRY}" PROPERTIES COMPILE_OPTIONS "/FI${MW34_PREP}/${MW34_LEVEL}/registry_build_bindings.hpp")
target_link_libraries(mw34_joint_startup54 PRIVATE bcrypt user32)
