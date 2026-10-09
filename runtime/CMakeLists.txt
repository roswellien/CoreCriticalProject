add_library(mw34_runtime STATIC memory/guest_memory.cpp)
target_compile_features(mw34_runtime PUBLIC cxx_std_20)
target_include_directories(mw34_runtime PUBLIC "${CMAKE_CURRENT_SOURCE_DIR}")
