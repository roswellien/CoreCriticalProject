cmake_minimum_required(VERSION 3.24)
project(MW34Recomp VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
if(NOT CMAKE_CONFIGURATION_TYPES AND NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Debug CACHE STRING "Build configuration" FORCE)
endif()

option(MW34_WARNINGS_AS_ERRORS "Treat project compiler warnings as errors" ON)
option(MW34_ENABLE_CLANG_TIDY "Run clang-tidy while compiling" OFF)
if(MW34_ENABLE_CLANG_TIDY)
    if(NOT CMAKE_GENERATOR MATCHES "Ninja|Makefiles")
        message(FATAL_ERROR "MW34_ENABLE_CLANG_TIDY requires a Ninja or Makefiles generator")
    endif()
    find_program(MW34_CLANG_TIDY clang-tidy REQUIRED)
    set(CMAKE_CXX_CLANG_TIDY "${MW34_CLANG_TIDY}")
endif()

include(cmake/Warnings.cmake)
add_subdirectory(runtime)
mw34_warnings(mw34_runtime)

include(CTest)
if(BUILD_TESTING)
    add_executable(mw34_runtime_tests tests/runtime_tests.cpp)
    target_link_libraries(mw34_runtime_tests PRIVATE mw34_runtime)
    mw34_warnings(mw34_runtime_tests)
    add_test(NAME runtime COMMAND mw34_runtime_tests)

    add_executable(mw34_mfc_receiver_tests tests/mfc_receiver_tests.cpp)
    target_link_libraries(mw34_mfc_receiver_tests PRIVATE mw34_runtime)
    mw34_warnings(mw34_mfc_receiver_tests)
    add_test(NAME mfc_receiver_lifecycle COMMAND mw34_mfc_receiver_tests)

    add_executable(mw34_joystick_selection_tests tools/remaster-launcher/test_joystick_selection.cpp)
    target_include_directories(mw34_joystick_selection_tests PRIVATE "${PROJECT_SOURCE_DIR}/tools/remaster-launcher")
    mw34_warnings(mw34_joystick_selection_tests)
    add_test(NAME joystick_selection COMMAND mw34_joystick_selection_tests)

    add_executable(mw34_material_normal_tests tools/remaster-launcher/test_material_normals.cpp)
    target_include_directories(mw34_material_normal_tests PRIVATE "${PROJECT_SOURCE_DIR}/runtime/graphics")
    target_compile_definitions(mw34_material_normal_tests PRIVATE _CRT_SECURE_NO_WARNINGS)
    mw34_warnings(mw34_material_normal_tests)
    add_test(NAME material_normals COMMAND mw34_material_normal_tests)
    add_test(NAME material_normals_disabled COMMAND mw34_material_normal_tests --maps-off)
    add_test(NAME world_normal_pages COMMAND mw34_material_normal_tests --world-pages)
    add_test(NAME world_normal_pages_disabled COMMAND mw34_material_normal_tests --world-pages-off)

    add_library(mw34_normal_hash SHARED tools/remaster-launcher/normal_hash.cpp)
    target_include_directories(mw34_normal_hash PRIVATE "${PROJECT_SOURCE_DIR}/runtime/graphics")
    target_compile_definitions(mw34_normal_hash PRIVATE _CRT_SECURE_NO_WARNINGS)
    mw34_warnings(mw34_normal_hash)

    add_executable(mw34_menu_wave_tests tools/remaster-launcher/test_menu_wave.cpp)
    target_include_directories(mw34_menu_wave_tests PRIVATE "${PROJECT_SOURCE_DIR}/runtime/graphics")
    mw34_warnings(mw34_menu_wave_tests)
    add_test(NAME menu_wave COMMAND mw34_menu_wave_tests)

    if(WIN32)
        add_executable(mw34_local_cd_audio_tests tests/local_cd_audio_tests.cpp)
        target_include_directories(mw34_local_cd_audio_tests PRIVATE "${PROJECT_SOURCE_DIR}/runtime")
        target_compile_definitions(mw34_local_cd_audio_tests PRIVATE _CRT_SECURE_NO_WARNINGS)
        target_link_libraries(mw34_local_cd_audio_tests PRIVATE winmm user32)
        mw34_warnings(mw34_local_cd_audio_tests)
        add_test(NAME local_cd_audio_failures COMMAND mw34_local_cd_audio_tests)

        add_executable(mw34_directinput_caps_tests tests/directinput_caps_tests.cpp)
        target_include_directories(mw34_directinput_caps_tests PRIVATE "${PROJECT_SOURCE_DIR}/runtime")
        mw34_warnings(mw34_directinput_caps_tests)
        add_test(NAME directinput_force_feedback_hidden COMMAND mw34_directinput_caps_tests)
    endif()

    find_package(Python3 3.11 REQUIRED COMPONENTS Interpreter)
    add_test(NAME native_host_build_metadata
        COMMAND "${Python3_EXECUTABLE}" -B
            "${PROJECT_SOURCE_DIR}/tools/m4-crt-heap-carry/test_host_build.py")
    add_test(NAME binary_tools
        COMMAND "${Python3_EXECUTABLE}" -m unittest discover -s tests -p test_binary_tools.py -v)
    set_tests_properties(binary_tools PROPERTIES WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")
    add_test(NAME release_and_mod_tools
        COMMAND "${Python3_EXECUTABLE}" -B -m unittest discover -s tests -p test_release_tools.py -v)
    set_tests_properties(release_and_mod_tools PROPERTIES WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")
    add_test(NAME pirates_moon_target_isolation
        COMMAND "${Python3_EXECUTABLE}" -B -m unittest discover -s tests -p test_pirates_moon.py -v)
    set_tests_properties(pirates_moon_target_isolation PROPERTIES WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")
    add_test(NAME asset_tools
        COMMAND "${Python3_EXECUTABLE}" -m unittest discover -s tests -p "test_asset*.py" -v)
    set_tests_properties(asset_tools PROPERTIES WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")
    add_test(NAME style_tools
        COMMAND "${Python3_EXECUTABLE}" -B -m unittest discover -s tests -p test_style_tools.py -v)
    set_tests_properties(style_tools PROPERTIES WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")
    add_test(NAME function_table
        COMMAND "${Python3_EXECUTABLE}" -B -m unittest discover -s tests -p test_function_table.py -v)
    set_tests_properties(function_table PROPERTIES WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")
    add_test(NAME in_game_hook_evidence
        COMMAND "${Python3_EXECUTABLE}" -m unittest discover -s tests -p test_in_game_hook.py -v)
    set_tests_properties(in_game_hook_evidence PROPERTIES WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")
    add_test(NAME pr_conventions
        COMMAND "${Python3_EXECUTABLE}" -B -m unittest discover -s tests -p test_pr_conventions.py -v)
    set_tests_properties(pr_conventions PROPERTIES WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")
    add_test(NAME board_check
        COMMAND "${Python3_EXECUTABLE}" -B -m unittest discover -s tests -p test_board_check.py -v)
    set_tests_properties(board_check PROPERTIES WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")
    add_test(NAME game_monitor
        COMMAND "${Python3_EXECUTABLE}" -m unittest discover -s tests -p test_game_monitor.py -v)
    set_tests_properties(game_monitor PROPERTIES WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")
    add_test(NAME game_monitor_invalid_handle
        COMMAND "${Python3_EXECUTABLE}" -m unittest discover -s tests -p test_monitor_invalid_handle.py -v)
    set_tests_properties(game_monitor_invalid_handle PROPERTIES WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")
    add_test(NAME mw3_comparison_controls
        COMMAND "${Python3_EXECUTABLE}" -m unittest discover -s tests -p test_mw3_comparison.py -v)
    set_tests_properties(mw3_comparison_controls PROPERTIES WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")
    add_test(NAME host_adapter_controls
        COMMAND "${Python3_EXECUTABLE}" -m unittest discover -s tests -p test_host_adapter.py -v)
    set_tests_properties(host_adapter_controls PROPERTIES WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")
    add_test(NAME agent_files
        COMMAND "${Python3_EXECUTABLE}" -B -m unittest discover -s tests -p test_agent_files.py -v)
    set_tests_properties(agent_files PROPERTIES WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")
endif()

find_program(MW34_CLANG_FORMAT clang-format)
if(MW34_CLANG_FORMAT)
    file(GLOB_RECURSE MW34_FORMAT_FILES CONFIGURE_DEPENDS
        "${PROJECT_SOURCE_DIR}/runtime/*.hpp" "${PROJECT_SOURCE_DIR}/runtime/*.cpp"
        "${PROJECT_SOURCE_DIR}/tests/*.cpp")
    add_custom_target(format
        COMMAND "${MW34_CLANG_FORMAT}" -i ${MW34_FORMAT_FILES}
        VERBATIM)
    add_custom_target(format-check
        COMMAND "${MW34_CLANG_FORMAT}" --dry-run --Werror ${MW34_FORMAT_FILES}
        VERBATIM)
endif()
