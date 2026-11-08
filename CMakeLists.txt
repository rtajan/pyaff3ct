cmake_minimum_required(VERSION 3.18)
cmake_policy(SET CMP0054 NEW)

project(pyaff3ct LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

set(CMAKE_THREAD_PREFER_PTHREAD ON)
set(THREADS_PREFER_PTHREAD_FLAG ON)
find_package(Threads REQUIRED)

# ------------------------------------------------------------------------------------------------- pybind11 & StreamPU
# pyaff3ct is an extension of pystreampu: it is built against the pybind11 and StreamPU versions of the installed
# `streampu` package (same pybind11 ABI, same StreamPU commit), see `streampu.get_cmake_dirs()`.
find_package(Python 3.10 COMPONENTS Interpreter Development.Module REQUIRED)
execute_process(
    COMMAND "${Python_EXECUTABLE}" -c
            "import os, streampu; print(streampu.get_cmake_dirs()); print(os.path.join(os.path.dirname(streampu._ext.__file__), 'include'))"
    OUTPUT_VARIABLE PYAF_STREAMPU_INFO
    OUTPUT_STRIP_TRAILING_WHITESPACE
    RESULT_VARIABLE PYAF_STREAMPU_FOUND)
if(NOT PYAF_STREAMPU_FOUND EQUAL 0)
    message(FATAL_ERROR "pyaff3ct - the 'streampu' Python package (pystreampu) is required to build pyaff3ct "
                        "(pip install streampu, then build with --no-build-isolation).")
endif()
string(REPLACE "\n" ";" PYAF_STREAMPU_INFO "${PYAF_STREAMPU_INFO}")
list(GET PYAF_STREAMPU_INFO 0 PYAF_STREAMPU_CMAKE_DIRS)
list(GET PYAF_STREAMPU_INFO 1 PYAF_PYSTREAMPU_INCLUDE_DIR)
if(WIN32)
    string(REPLACE ";" "\\;" PYAF_STREAMPU_CMAKE_DIRS "${PYAF_STREAMPU_CMAKE_DIRS}")
else()
    string(REPLACE ":" ";" PYAF_STREAMPU_CMAKE_DIRS "${PYAF_STREAMPU_CMAKE_DIRS}")
endif()
list(APPEND CMAKE_PREFIX_PATH ${PYAF_STREAMPU_CMAKE_DIRS})
message(STATUS "pyaff3ct - pystreampu CMake dirs: ${PYAF_STREAMPU_CMAKE_DIRS}")
message(STATUS "pyaff3ct - pystreampu headers: ${PYAF_PYSTREAMPU_INCLUDE_DIR}")

set(PYBIND11_NEWPYTHON ON)
find_package(pybind11 3.0.4 CONFIG REQUIRED)
find_package(cpptrace CONFIG REQUIRED) # dependency of the StreamPU targets (spu::spu-static-lib)
# pystreampu built with Julia (SPU_LINK_JULIA=ON): its StreamPU links Julia::Julia, defined by the CMake package
# "Julia" that pystreampu installs next to the one of StreamPU (same CMAKE_PREFIX_PATH). Nothing otherwise.
find_package(Julia 1.10.9 QUIET)
find_package(StreamPU CONFIG REQUIRED)
if(Julia_FOUND)
    message(STATUS "pyaff3ct - pystreampu is built with Julia: ${JULIA_LIBRARY}")
endif()
message(STATUS "pyaff3ct - StreamPU: ${StreamPU_DIR} (version ${StreamPU_VERSION})")

# --------------------------------------------------------------------------------------------------------------- AFF3CT
if(NOT EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/lib/aff3ct/CMakeLists.txt")
    message(FATAL_ERROR "pyaff3ct - AFF3CT can't be found, run: git submodule update --init --recursive lib/aff3ct")
endif()
# SIMD baseline (AFF3CT and the wrapper must agree): MIPP aborts at run time with the x86-64 SSE2 baseline, so the
# default is SSE4.2 on x86-64, as the official AFF3CT packages (ppa). Use e.g. -DPYAFF3CT_ARCH_FLAGS=-march=native
# for a local build tuned for the host.
if(CMAKE_SYSTEM_PROCESSOR MATCHES "^(x86_64|AMD64|amd64)$")
    set(PYAF_DEFAULT_ARCH_FLAGS "-msse4.2")
else()
    set(PYAF_DEFAULT_ARCH_FLAGS "")
endif()
set(PYAFF3CT_ARCH_FLAGS "${PYAF_DEFAULT_ARCH_FLAGS}" CACHE STRING "Architecture flags of AFF3CT and the wrapper")
if(PYAFF3CT_ARCH_FLAGS)
    separate_arguments(PYAF_ARCH_FLAGS_LIST UNIX_COMMAND "${PYAFF3CT_ARCH_FLAGS}")
    add_compile_options(${PYAF_ARCH_FLAGS_LIST})
    message(STATUS "pyaff3ct - Architecture flags: ${PYAFF3CT_ARCH_FLAGS}")
endif()

set(AFF3CT_COMPILE_EXE OFF CACHE BOOL "" FORCE)
set(AFF3CT_COMPILE_STATIC_LIB ON CACHE BOOL "" FORCE)
set(AFF3CT_COMPILE_SHARED_LIB OFF CACHE BOOL "" FORCE)
set(AFF3CT_PREC "MULTI" CACHE STRING "" FORCE)            # every precision: the dtype is chosen at runtime
set(AFF3CT_INCLUDE_SPU_LIB OFF CACHE BOOL "" FORCE)       # use the StreamPU of pystreampu
set(AFF3CT_EXT_STRINGS OFF CACHE BOOL "" FORCE)           # help strings compiled in (self-contained wheel)
add_subdirectory(lib/aff3ct EXCLUDE_FROM_ALL)

# ----------------------------------------------------------------------------------------------------------- aff3ct._ext
file(GLOB_RECURSE PYAF_SOURCES CONFIGURE_DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/internal/src/*.cpp")
file(GLOB_RECURSE PYAF_HEADERS CONFIGURE_DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/internal/include/*")
pybind11_add_module(_ext MODULE ${PYAF_SOURCES} ${PYAF_HEADERS})
# pystreampu installs its wrapper headers in <streampu>/include/pystreampu ("wrapper/Common/...")
target_include_directories(_ext PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/internal/include"
                                        "${PYAF_PYSTREAMPU_INCLUDE_DIR}/pystreampu")
target_link_libraries(_ext PRIVATE aff3ct-static-lib Threads::Threads)
if(Julia_FOUND AND JULIA_LIBRARY)
    # libjulia found at import time
    get_filename_component(PYAF_JULIA_LIBRARY_DIR "${JULIA_LIBRARY}" DIRECTORY)
    set_property(TARGET _ext APPEND PROPERTY BUILD_RPATH "${PYAF_JULIA_LIBRARY_DIR}")
    set_property(TARGET _ext APPEND PROPERTY INSTALL_RPATH "${PYAF_JULIA_LIBRARY_DIR}")
endif()

option(PYAFF3CT_WERROR "Treat the warnings of the wrapper as errors" OFF)
if(PYAFF3CT_WERROR)
    target_compile_options(_ext PRIVATE -Werror)
endif()

install(TARGETS _ext DESTINATION .)
