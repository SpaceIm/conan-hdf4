import os

from conans import ConanFile, CMake, tools

class Hdf4Conan(ConanFile):
    name = "hdf4"
    description = "HDF4 is a data model, library, and file format for storing and managing data."
    license = "BSD-3-Clause"
    topics = ("conan", "hdf4", "hdf", "data")
    homepage = "https://portal.hdfgroup.org/display/HDF4/HDF4"
    url = "https://github.com/conan-io/conan-center-index"
    exports_sources = "CMakeLists.txt"
    generators = "cmake"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "szip_support": ["None", "with_libaec", "with_szip"]
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "szip_support": "None"
    }

    _cmake = None

    @property
    def _source_subfolder(self):
        return "source_subfolder"

    @property
    def _build_subfolder(self):
        return "build_subfolder"

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        del self.settings.compiler.libcxx
        del self.settings.compiler.cppstd

    def requirements(self):
        self.requires.add("libjpeg/9d")
        self.requires.add("zlib/1.2.11")
        if self.options.szip_support == "with_libaec":
            self.requires.add("libaec/1.0.4")
        elif self.options.szip_support == "with_szip":
            self.requires.add("szip/2.1.1")

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        os.rename("hdf-" + self.version, self._source_subfolder)

    def build(self):
        cmake = self._configure_cmake()
        cmake.build()

    def _configure_cmake(self):
        if self._cmake:
            return self._cmake
        self._cmake = CMake(self)
        self._cmake.definitions["HDF4_EXTERNALLY_CONFIGURED"] = True
        self._cmake.definitions["HDF4_EXTERNAL_LIB_PREFIX"] = ""
        self._cmake.definitions["HDF4_USE_FOLDERS"] = True
        self._cmake.definitions["HDF4_NO_PACKAGES"] = True
        self._cmake.definitions["ONLY_SHARED_LIBS"] = self.options.shared
        self._cmake.definitions["HDF4_ENABLE_COVERAGE"] = False
        self._cmake.definitions["HDF4_ENABLE_DEPRECATED_SYMBOLS"] = True
        self._cmake.definitions["HDF4_ENABLE_JPEG_LIB_SUPPORT"] = True # HDF can't compile without libjpeg
        self._cmake.definitions["HDF4_ENABLE_Z_LIB_SUPPORT"] = True # HDF can't compile without zlib
        self._cmake.definitions["HDF4_ENABLE_SZIP_SUPPORT"] = self.options.szip_support != "None"
        if self.options.szip_support == "with_libaec":
            self._cmake.definitions["HDF4_ENABLE_SZIP_ENCODING"] = True
        elif self.options.szip_support == "with_szip":
            self._cmake.definitions["HDF4_ENABLE_SZIP_ENCODING"] = self.options["szip"].enable_encoding
        self._cmake.definitions["HDF4_PACKAGE_EXTLIBS"] = False
        self._cmake.definitions["HDF4_BUILD_XDR_LIB"] = True
        self._cmake.definitions["BUILD_TESTING"] = False
        self._cmake.definitions["HDF4_BUILD_FORTRAN"] = False
        self._cmake.definitions["HDF4_BUILD_UTILS"] = False
        self._cmake.definitions["HDF4_BUILD_TOOLS"] = False
        self._cmake.definitions["HDF4_BUILD_EXAMPLES"] = False
        self._cmake.definitions["HDF4_BUILD_JAVA"] = False
        self._cmake.configure(build_folder=self._build_subfolder)
        return self._cmake

    def package(self):
        self.copy("COPYING", dst="licenses", src=self._source_subfolder)
        cmake = self._configure_cmake()
        cmake.install()
        tools.rmdir(os.path.join(self.package_folder, "lib", "pkgconfig"))
        os.remove(os.path.join(self.package_folder, "lib", "libhdf4.settings"))

    def package_info(self):
        libs = ["mfhdf", "xdr", "hdf"]
        if self.settings.os == "Windows" and not self.options.shared:
            libs = ["lib" + lib for lib in libs]
        if self.settings.build_type == "Debug":
            libs = [lib + "_debug" for lib in libs]
        self.cpp_info.libs = libs
        if self.options.shared:
            self.cpp_info.defines.append("H4_BUILT_AS_DYNAMIC_LIB")
