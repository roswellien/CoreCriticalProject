cmake_minimum_required(VERSION 3.24)
project(MW34CarryPeer LANGUAGES CXX)
if(NOT WIN32 OR NOT CMAKE_SIZEOF_VOID_P EQUAL 8 OR NOT CMAKE_CXX_COMPILER_ID MATCHES "Clang" OR NOT PEER_OBJECTS)
  message(FATAL_ERROR "Peer controls require Windows AMD64 and exact frozen object list")
endif()
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
add_subdirectory(../../runtime runtime)
file(GLOB FP_CPP "${PEER_DERIVED}/native/*.cpp")
add_executable(carry_peer causal.cpp ${FP_CPP}
  "${PEER_DERIVED}/native/chain/runtime_adapter.cpp" "${PEER_DERIVED}/native/integer/runtime_adapter.cpp"
  ../m4-initializer-chain/component.cpp ../m4-integer-startup/component.cpp
  ../m4-runtime/runtime.cpp ../m4-startup/image_loader.cpp ../m4-guest-cw/guest_cw.cpp ${PEER_OBJECTS})
target_include_directories(carry_peer PRIVATE ../m4-crt-control-carry ../m4-runtime ../m4-startup ../m4-guest-cw ../m4-crt
  "${PEER_DERIVED}/native" "${PEER_DERIVED}/original" "${PEER_BINDINGS}" ../../runtime)
target_include_directories(carry_peer SYSTEM PRIVATE "${PEER_REMILL}")
target_compile_definitions(carry_peer PRIVATE ADDRESS_SIZE_BITS=32 HAS_FEATURE_AVX=0 HAS_FEATURE_AVX512=0)
target_compile_options(carry_peer PRIVATE /EHsc /clang:-frounding-math)
target_link_libraries(carry_peer PRIVATE mw34_runtime bcrypt)
