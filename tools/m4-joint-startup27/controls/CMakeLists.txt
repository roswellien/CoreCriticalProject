cmake_minimum_required(VERSION 3.24)
project(MW34JointStartup27Controls LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
string(REPLACE "/EHsc" "" CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS}")
if(NOT MW34_ROOT OR NOT MW34_DERIVED OR NOT MW34_BINDINGS OR NOT MW34_OBJECTS)
 message(FATAL_ERROR "Exact frozen worker, derivatives, bindings and guest objects required")
endif()
file(GLOB MW34_FP_CPP "${MW34_DERIVED}/derived/*.cpp")
set(MW34_FIXTURE fixture.cpp)
if(MW34_DIAGNOSTIC)
 set(MW34_FIXTURE diagnostic.cpp)
endif()
add_executable(mw34_joint27_controls ${MW34_FIXTURE} ${MW34_FP_CPP}
 "${MW34_DERIVED}/derived/chain/runtime_adapter.cpp" "${MW34_DERIVED}/derived/integer/runtime_adapter.cpp"
 "${MW34_ROOT}/tools/m4-initializer-chain/component.cpp" "${MW34_ROOT}/tools/m4-integer-startup/component.cpp"
 "${MW34_ROOT}/tools/m4-runtime/runtime.cpp" "${MW34_ROOT}/tools/m4-startup/image_loader.cpp"
 "${MW34_ROOT}/runtime/memory/guest_memory.cpp" ${MW34_OBJECTS})
target_include_directories(mw34_joint27_controls PRIVATE "${MW34_DERIVED}" "${MW34_BINDINGS}"
 "${MW34_ROOT}/tools/m4-runtime" "${MW34_ROOT}/tools/m4-startup" "${MW34_ROOT}/runtime" "${MW34_ROOT}/tools/m4-fp-numeric-max")
target_include_directories(mw34_joint27_controls SYSTEM PRIVATE "${MW34_ROOT}/local/tools/remill-v6.0.1/remill-6.0.1/include")
target_compile_definitions(mw34_joint27_controls PRIVATE ADDRESS_SIZE_BITS=32 HAS_FEATURE_AVX=0 HAS_FEATURE_AVX512=0)
target_compile_options(mw34_joint27_controls PRIVATE /EHs /clang:-frounding-math)
target_link_libraries(mw34_joint27_controls PRIVATE bcrypt)
