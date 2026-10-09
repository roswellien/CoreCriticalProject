cmake_minimum_required(VERSION 3.24)
project(MW34ControlCarryNative LANGUAGES CXX)
if(NOT WIN32 OR NOT CMAKE_CXX_COMPILER_ID MATCHES "Clang" OR NOT CMAKE_SIZEOF_VOID_P EQUAL 8 OR NOT MW34_DERIVED OR NOT MW34_OBJECTS OR NOT MW34_REMILL_INCLUDE)
  message(FATAL_ERROR "Fresh carry worker requires exact Windows x64 static dependencies")
endif()
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
add_subdirectory("${CMAKE_CURRENT_SOURCE_DIR}/../../../runtime" runtime)
file(GLOB MW34_FP_CPP "${MW34_DERIVED}/native/*.cpp")
add_executable(mw34_control_carry_native ../native_main.cpp ${MW34_FP_CPP}
  "${MW34_DERIVED}/native/chain/runtime_adapter.cpp" "${MW34_DERIVED}/native/integer/runtime_adapter.cpp"
  ../../m4-initializer-chain/component.cpp ../../m4-integer-startup/component.cpp
  ../../m4-runtime/runtime.cpp ../../m4-startup/image_loader.cpp ../../m4-guest-cw/guest_cw.cpp ${MW34_OBJECTS})
target_include_directories(mw34_control_carry_native PRIVATE .. ../../m4-runtime ../../m4-startup ../../m4-guest-cw ../../m4-crt "${MW34_DERIVED}/native" "${MW34_DERIVED}/original" "${MW34_BINDINGS}" "${CMAKE_CURRENT_SOURCE_DIR}/../../../runtime")
target_include_directories(mw34_control_carry_native SYSTEM PRIVATE "${MW34_REMILL_INCLUDE}")
target_compile_definitions(mw34_control_carry_native PRIVATE ADDRESS_SIZE_BITS=32 HAS_FEATURE_AVX=0 HAS_FEATURE_AVX512=0)
target_compile_options(mw34_control_carry_native PRIVATE /EHsc /clang:-frounding-math)
target_link_libraries(mw34_control_carry_native PRIVATE mw34_runtime bcrypt)
