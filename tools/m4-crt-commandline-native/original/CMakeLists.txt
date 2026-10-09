cmake_minimum_required(VERSION 3.24)
project(MW34ActualCommandLineOriginal LANGUAGES CXX ASM_MASM)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
add_executable(commandline_original ../original_worker.cpp ../original_x86.asm ../../m4-startup/image_loader.cpp ../../../runtime/memory/guest_memory.cpp)
target_include_directories(commandline_original PRIVATE "${MW34_COMMANDLINE_INCLUDE}" ../../m4-runtime ../../m4-startup ../../../runtime)
target_link_libraries(commandline_original PRIVATE bcrypt)

# Keep the original broker executable away from exact guest IAT reservation.
target_link_options(commandline_original PRIVATE /DYNAMICBASE:NO /BASE:0x00400000)
