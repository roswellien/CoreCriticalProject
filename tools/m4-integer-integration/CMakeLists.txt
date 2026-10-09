cmake_minimum_required(VERSION 3.24)
project(MW34CombinedIntegerStartup LANGUAGES CXX)
if(NOT WIN32 OR NOT CMAKE_CXX_COMPILER_ID MATCHES "Clang" OR NOT CMAKE_SIZEOF_VOID_P EQUAL 8 OR NOT MW34_CHAIN_OBJECT OR NOT MW34_INTEGER_OBJECT OR NOT MW34_REMILL_INCLUDE)
  message(FATAL_ERROR "Combined host requires Windows x64 Clang and exact two compiled guest objects")
endif()
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
add_subdirectory("${CMAKE_CURRENT_SOURCE_DIR}/../../runtime" runtime)
add_executable(mw34_m4_integer_host main.cpp
  ../m4-initializer-chain/runtime_adapter.cpp ../m4-initializer-chain/component.cpp
  ../m4-integer-startup/runtime_adapter.cpp ../m4-integer-startup/component.cpp
  ../m4-runtime/runtime.cpp ../m4-startup/image_loader.cpp
  "${MW34_CHAIN_OBJECT}" "${MW34_INTEGER_OBJECT}")
target_include_directories(mw34_m4_integer_host PRIVATE ../m4-runtime ../m4-startup)
target_include_directories(mw34_m4_integer_host SYSTEM PRIVATE "${MW34_REMILL_INCLUDE}")
target_compile_definitions(mw34_m4_integer_host PRIVATE ADDRESS_SIZE_BITS=32 HAS_FEATURE_AVX=0 HAS_FEATURE_AVX512=0)
target_compile_options(mw34_m4_integer_host PRIVATE /EHsc)
target_link_libraries(mw34_m4_integer_host PRIVATE mw34_runtime bcrypt)
