cmake_minimum_required(VERSION 3.24)
project(MW34VideoCreationFixture LANGUAGES CXX)

# Isolated authored fixture: no shared startup gate or verifier build is changed.
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(MW34_WARNINGS_AS_ERRORS ON)
include("${CMAKE_CURRENT_LIST_DIR}/../../cmake/Warnings.cmake")
add_executable(m4_video_creation_fixture
    "${CMAKE_CURRENT_LIST_DIR}/../../tests/video_creation_tests.cpp"
    "${CMAKE_CURRENT_LIST_DIR}/../../runtime/graphics/direct_draw_creation.cpp"
    "${CMAKE_CURRENT_LIST_DIR}/../../runtime/memory/guest_memory.cpp")
target_include_directories(m4_video_creation_fixture PRIVATE
    "${CMAKE_CURRENT_LIST_DIR}/../../runtime")
mw34_warnings(m4_video_creation_fixture)
enable_testing()
add_test(NAME video_creation_authored_fixture COMMAND m4_video_creation_fixture)
