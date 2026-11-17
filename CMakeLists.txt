cmake_minimum_required(VERSION 3.23)
project(arinc653_lab LANGUAGES C CXX)
set(CMAKE_C_STANDARD 99)
set(CMAKE_CXX_STANDARD 17)
find_package(Threads REQUIRED)
set(V ${CMAKE_CURRENT_SOURCE_DIR}/third_party/a653lib)
# Deliberate native subset: no generated AEEC headers, Wasm or upstream launcher.
add_library(apex SHARED
  ${V}/a653_lib/a653_i_partition.c ${V}/a653_lib/a653_i_process.c
  ${V}/a653_lib/a653_i_queuing.c ${V}/a653_lib/a653_i_sampling.c
  ${V}/a653_lib/a653_i_time.c ${V}/a653_lib/a653_i_time_lib.c)
target_include_directories(apex PUBLIC ${V}/a653_inc ${V}/a653_lib backend)
target_link_libraries(apex PUBLIC Threads::Threads)
add_executable(lab_runner backend/runner.cpp ${CMAKE_BINARY_DIR}/config.c)
target_link_libraries(lab_runner PRIVATE apex dl)
target_link_options(lab_runner PRIVATE -rdynamic)
include(${CMAKE_BINARY_DIR}/partitions.cmake)
