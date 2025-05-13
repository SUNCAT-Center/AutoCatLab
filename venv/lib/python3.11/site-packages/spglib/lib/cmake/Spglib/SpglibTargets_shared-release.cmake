#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "Spglib::symspg" for configuration "Release"
set_property(TARGET Spglib::symspg APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(Spglib::symspg PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libsymspg.2.6.0.dylib"
  IMPORTED_SONAME_RELEASE "@rpath/libsymspg.2.dylib"
  )

list(APPEND _cmake_import_check_targets Spglib::symspg )
list(APPEND _cmake_import_check_files_for_Spglib::symspg "${_IMPORT_PREFIX}/lib/libsymspg.2.6.0.dylib" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
