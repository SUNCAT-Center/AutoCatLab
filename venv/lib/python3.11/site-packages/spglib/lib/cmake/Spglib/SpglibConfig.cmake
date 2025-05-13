
####### Expanded from @PACKAGE_INIT@ by configure_package_config_file() #######
####### Any changes to this file will be overwritten by the next CMake run ####
####### The input file was SpglibConfig.cmake.in                            ########

get_filename_component(PACKAGE_PREFIX_DIR "${CMAKE_CURRENT_LIST_DIR}/../../../" ABSOLUTE)

macro(set_and_check _var _file)
  set(${_var} "${_file}")
  if(NOT EXISTS "${_file}")
    message(FATAL_ERROR "File or directory ${_file} referenced by variable ${_var} does not exist !")
  endif()
endmacro()

macro(check_required_components _NAME)
  foreach(comp ${${_NAME}_FIND_COMPONENTS})
    if(NOT ${_NAME}_${comp}_FOUND)
      if(${_NAME}_FIND_REQUIRED_${comp})
        set(${_NAME}_FOUND FALSE)
      endif()
    endif()
  endforeach()
endmacro()

####################################################################################


## Define basic variables
# Defined components in the project
set(Spglib_Supported_Comps static shared omp fortran)
# Define deprecated components. For each deprecated component define ${comp}_Replacement
set(Spglib_Deprecated_Comps "")
set(Spglib_VERSION_FULL 2.6.0)
set(Spglib_COMMIT c633404d67b2aa341ae748819c542e81c0c1f55d)
set(Spglib_Fortran OFF)
set(Spglib_Python OFF)
set(Spglib_OMP OFF)
set(Spglib_LIB_TYPE )

# Workaround for pip build isolation issue
# https://github.com/pypa/pip/issues/12976
# Check that this installation is built within scikit-build-core
# and that wer are rebuilding the same spglib python project
set(_spglib_built_from_skbuild_project "spglib")
if(_spglib_built_from_skbuild_project STREQUAL "spglib" AND
    SKBUILD_PROJECT_NAME STREQUAL "spglib")
	set(Spglib_FOUND FALSE)
	return()
endif()

## Parse find_package request

if (NOT EXISTS ${CMAKE_CURRENT_LIST_DIR}/PackageCompsHelper.cmake)
	message(WARNING "Missing helper file PackageCompsHelper.cmake")
	set(Spglib_FOUND FALSE)
	return()
endif ()

include(${CMAKE_CURRENT_LIST_DIR}/PackageCompsHelper.cmake)
find_package_with_comps(PACKAGE Spglib PRINT LOAD_ALL_DEFAULT HAVE_GLOBAL_SHARED_STATIC)

check_required_components(Spglib)

get_property(languages GLOBAL PROPERTY ENABLED_LANGUAGES)
# For Fortran targets, check that the modules are usable with the current compiler
if (Fortran IN_LIST languages AND TARGET Spglib::fortran_mod)
	try_compile(spglib_fortran_try_compile
			SOURCES ${CMAKE_CURRENT_LIST_DIR}/try_compile.f90
			LINK_LIBRARIES Spglib::fortran_mod
	)
	if (spglib_fortran_try_compile)
		# If the compilation was successful, use the module version of the library
		add_library(Spglib::fortran ALIAS Spglib::fortran_mod)
	else ()
		# Otherwise, assume it was because of incompatible compiler
		# Add the bundled `.f90` files as sources instead
		add_library(Spglib::fortran ALIAS Spglib::fortran_include)
	endif ()
endif ()
