cmake_minimum_required(VERSION 3.24)
project(MW34Joint27 LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
string(REPLACE "/EHsc" "" CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS}")
if(NOT MW34_DERIVED OR NOT MW34_BINDINGS OR NOT MW34_OBJECTS)
 message(FATAL_ERROR "Exact prepared joint27 derivatives and compiled objects required")
endif()
file(GLOB MW34_FP_CPP "${MW34_DERIVED}/derived/*.cpp")
add_executable(mw34_joint27 native_main.cpp ${MW34_FP_CPP}
 "${MW34_DERIVED}/derived/chain/runtime_adapter.cpp" "${MW34_DERIVED}/derived/integer/runtime_adapter.cpp"
 ../m4-initializer-chain/component.cpp ../m4-integer-startup/component.cpp ../m4-runtime/runtime.cpp ../m4-startup/image_loader.cpp
 ../../runtime/memory/guest_memory.cpp ${MW34_OBJECTS})
target_include_directories(mw34_joint27 PRIVATE "${MW34_DERIVED}" "${MW34_BINDINGS}" ../m4-runtime ../m4-startup ../../runtime ../m4-fp-numeric-max)
target_include_directories(mw34_joint27 SYSTEM PRIVATE ../../local/tools/remill-v6.0.1/remill-6.0.1/include)
target_compile_definitions(mw34_joint27 PRIVATE ADDRESS_SIZE_BITS=32 HAS_FEATURE_AVX=0 HAS_FEATURE_AVX512=0)
target_compile_options(mw34_joint27 PRIVATE /EHs /clang:-frounding-math)
target_link_libraries(mw34_joint27 PRIVATE bcrypt)
