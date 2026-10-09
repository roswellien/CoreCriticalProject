cmake_minimum_required(VERSION 3.24)
project(MW34MixedStartupCandidate LANGUAGES CXX)
if(NOT WIN32 OR NOT CMAKE_CXX_COMPILER_ID MATCHES "Clang" OR NOT CMAKE_SIZEOF_VOID_P EQUAL 8 OR NOT MW34_DERIVED OR NOT MW34_OBJECTS OR NOT MW34_REMILL_INCLUDE)
  message(FATAL_ERROR "Fresh mixed candidate requires exact Windows x64 static dependencies")
endif()
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
add_subdirectory("${CMAKE_CURRENT_SOURCE_DIR}/../../runtime" runtime)
file(GLOB MW34_FP_CPP "${MW34_DERIVED}/*.cpp")
add_executable(mw34_m4_mixed_native native_main.cpp ${MW34_FP_CPP}
  "${MW34_DERIVED}/chain/runtime_adapter.cpp" "${MW34_DERIVED}/integer/runtime_adapter.cpp"
  ../m4-initializer-chain/component.cpp ../m4-integer-startup/component.cpp
  ../m4-runtime/runtime.cpp ../m4-startup/image_loader.cpp ${MW34_OBJECTS})
target_include_directories(mw34_m4_mixed_native PRIVATE ../m4-runtime ../m4-startup "${MW34_BINDINGS}" "${CMAKE_CURRENT_SOURCE_DIR}/../../runtime")
target_include_directories(mw34_m4_mixed_native SYSTEM PRIVATE "${MW34_REMILL_INCLUDE}")
target_compile_definitions(mw34_m4_mixed_native PRIVATE ADDRESS_SIZE_BITS=32 HAS_FEATURE_AVX=0 HAS_FEATURE_AVX512=0)
target_compile_options(mw34_m4_mixed_native PRIVATE /EHsc /clang:-frounding-math)
target_link_libraries(mw34_m4_mixed_native PRIVATE mw34_runtime bcrypt)
