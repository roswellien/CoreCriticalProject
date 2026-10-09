cmake_minimum_required(VERSION 3.24)
project(MW34CRTDataReferenceOwnership LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
get_filename_component(MW34_WORKSPACE "${CMAKE_CURRENT_SOURCE_DIR}/../../.." ABSOLUTE)
if(NOT WIN32 OR NOT CMAKE_SIZEOF_VOID_P EQUAL 8)
  message(FATAL_ERROR "Reference data ownership gate targets Windows AMD64")
endif()
foreach(level O0 O2)
  add_library(data_reference_${level} STATIC
    ../data_imports.cpp
    "${MW34_WORKSPACE}/tools/m4-runtime/runtime.cpp"
    "${MW34_WORKSPACE}/tools/m4-startup/image_loader.cpp"
    "${MW34_WORKSPACE}/runtime/memory/guest_memory.cpp")
  target_include_directories(data_reference_${level} PUBLIC
    "${CMAKE_CURRENT_SOURCE_DIR}/.." "${MW34_WORKSPACE}/tools/m4-runtime"
    "${MW34_WORKSPACE}/tools/m4-startup" "${MW34_WORKSPACE}/runtime")
  target_link_libraries(data_reference_${level} PUBLIC bcrypt)
  add_executable(data_reference_tests_${level} "${MW34_WORKSPACE}/tests/m4-crt-data/ownership_tests.cpp")
  target_link_libraries(data_reference_tests_${level} PRIVATE data_reference_${level})
  foreach(target data_reference_${level} data_reference_tests_${level})
    # Frozen Runtime deliberately aligns complete architectural State storage.
    # MSVC C4324 only reports that required padding; keep all other warnings fatal.
    target_compile_options(${target} PRIVATE /W4 /WX /wd4324 /permissive-)
    if(level STREQUAL O0)
      target_compile_options(${target} PRIVATE /Od)
    else()
      target_compile_options(${target} PRIVATE /O2)
    endif()
  endforeach()
endforeach()
