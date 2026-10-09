cmake_minimum_required(VERSION 3.24)
project(MW34JointStartup28 LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
string(REPLACE "/EHsc" "" CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS}")
if(NOT MW34_ROOT OR NOT MW34_PREP OR NOT MW34_LEVEL OR NOT MW34_OBJECTS OR NOT MW34_WRITER)
 message(FATAL_ERROR "Exact frozen preparation/level/literal objects/canonical writer required")
endif()
file(GLOB MW34_FP_CPP "${MW34_PREP}/derived/*.cpp")
add_executable(mw34_joint_startup28 "${MW34_PREP}/native_main.cpp" ${MW34_FP_CPP}
 "${MW34_PREP}/derived/chain/runtime_adapter.cpp" "${MW34_PREP}/derived/integer/runtime_adapter.cpp"
 "${MW34_ROOT}/tools/m4-initializer-chain/component.cpp" "${MW34_ROOT}/tools/m4-integer-startup/component.cpp"
 "${MW34_ROOT}/tools/m4-runtime/runtime.cpp" "${MW34_ROOT}/tools/m4-startup/image_loader.cpp"
 "${MW34_ROOT}/runtime/memory/guest_memory.cpp" ${MW34_OBJECTS} "${MW34_WRITER}" "${MW34_ROOT}/reports/m4-capture-direct/build-r4/preserve.obj")
target_include_directories(mw34_joint_startup28 PRIVATE "${MW34_PREP}" "${MW34_PREP}/${MW34_LEVEL}"
 "${MW34_ROOT}/tools/m4-runtime" "${MW34_ROOT}/tools/m4-startup" "${MW34_ROOT}/runtime" "${MW34_ROOT}/tools/m4-fp-numeric-max")
target_include_directories(mw34_joint_startup28 SYSTEM PRIVATE "${MW34_ROOT}/local/tools/remill-v6.0.1/remill-6.0.1/include")
target_compile_definitions(mw34_joint_startup28 PRIVATE ADDRESS_SIZE_BITS=32 HAS_FEATURE_AVX=0 HAS_FEATURE_AVX512=0)
target_compile_options(mw34_joint_startup28 PRIVATE /EHs /clang:-frounding-math)
target_link_libraries(mw34_joint_startup28 PRIVATE bcrypt user32)
