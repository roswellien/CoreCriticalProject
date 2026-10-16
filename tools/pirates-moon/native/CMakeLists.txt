cmake_minimum_required(VERSION 3.24)
project(MW34PiratesMoonNative LANGUAGES CXX)
get_filename_component(MW34_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../../.." ABSOLUTE)
if(NOT MW34_PM_GENERATED)
    message(FATAL_ERROR "PM verified generated profile/dispatch directory required")
endif()
add_subdirectory("${MW34_ROOT}/tools/m4-crt-heap-carry/native" shared-host)
set_target_properties(entry_commandline PROPERTIES OUTPUT_NAME pirates_moon_native)
target_compile_definitions(entry_commandline PRIVATE
    MW34_NATIVE_TARGET_PROFILE="${MW34_PM_GENERATED}/target.inc"
    MW34_MFC_ENTRIES_HEADER="${MW34_PM_GENERATED}/entries.inc"
    MW34_MFC_ROUTERS_HEADER="${MW34_PM_GENERATED}/routers.inc"
    MW34_NATIVE_TARGET_MAIN="${MW34_ROOT}/tools/pirates-moon/native_main.inc")
