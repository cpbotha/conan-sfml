# sfml conanfile - modified by cpbotha from original by TyRoXx
# * use SFML-2.3.2
# * use tarball instead of zip to work-around symlink bug
#   https://github.com/conan-io/conan/issues/336

from conans import ConanFile
import os
from conans.tools import download, unzip, check_sha256
from conans import CMake
import platform


class SFMLConanFile(ConanFile):
    name = "sfml"
    version = "2.3.2"
    branch = "stable"
    settings = "os", "compiler", "arch", "build_type"
    options = {"shared": [True, False]}
    default_options = "shared=True"
    generators = "cmake"
    license = "zlib/png"
    url = "http://github.com/cpbotha/conan-sfml"
    exports = ["CMakeLists.txt"]
    ZIP_FOLDER_NAME = "SFML-2.3.2"
    so_version = '2.3'

    def source(self):
        tgz_name = "2.3.2.tar.gz"
        download("https://github.com/SFML/SFML/archive/%s" % tgz_name, tgz_name)
        check_sha256(tgz_name, "55e7c864938e03ceb7d6d05c66f8e0dc886e632805d0ae17c222da317ba14e4c")
        # unzip falls back to untargz in the case of tar.gz extension
        unzip(tgz_name)
        os.unlink(tgz_name)

    def build(self):
        cmake = CMake(self.settings)
        self.run("mkdir _build")
        # put frameworks in ~/Library/Frameworks, else we get permission denied
        # for SFML to work, you'll probably have to copy the sfml extlibs
        # frameworks manually into /Library/Frameworks
        self.run('cd _build && cmake ../%s -DBUILD_SHARED_LIBS=%s -DCMAKE_INSTALL_PREFIX=../install -DCMAKE_INSTALL_FRAMEWORK_PREFIX=../install/Frameworks %s' %
            (self.ZIP_FOLDER_NAME, "ON" if self.options.shared else "OFF", cmake.command_line)
        )
        if self.settings.os == "Windows":
            self.run("cd _build && cmake --build . %s --target install --config %s" % (cmake.build_config, self.settings.build_type))
        else:
            self.run("cd _build && cmake --build . %s -- -j2 install" % cmake.build_config)

    def package(self):
        self.copy("*.*", "include", "install/include", keep_path=True)
        self.copy("*.*", "Frameworks", "install/Frameworks", keep_path=True)
        # actually just copy everything in the lib directory
        # it's a shame that conan does not preserve symbolic links in this case
        # https://github.com/conan-io/conan/issues/204
        # but I guess we'll live.
        self.copy(pattern="*.*", dst="lib", src="install/lib", keep_path=False)
        #self.copy(pattern="*.so." + self.so_version, dst="lib", src="install/lib", keep_path=False)
        #self.copy(pattern="*.lib", dst="lib", src="install/lib", keep_path=False)
        #self.copy(pattern="*.dylib", dst="lib", src="install/lib", keep_path=False)
        self.copy(pattern="*.dll", dst="bin", src="install/lib", keep_path=False)

    def package_info(self):
        if (not self.settings.os == "Windows") and self.options.shared:
            # on Macos, we do e.g. -lsfml-audio.2.3 to link to libsfml-audio.2.3.dylib
            # on Linux, it's just -lsfml-audio to link to libsfml-audio.so which is a symlink
            # using platform.system() instead of self.settings.os here
            # to work around https://github.com/conan-io/conan/issues/338
            if platform.system() == "Linux":
                so_version = ''
            else:
                so_version = '.' + self.so_version

            self.cpp_info.libs = map(
                lambda name: name + ('-d' if self.settings.build_type == "Debug" else '') + so_version,
                ['sfml-audio', 'sfml-graphics', 'sfml-network', 'sfml-window', 'sfml-system']
            )
        else:
            self.cpp_info.libs = map(
                lambda name: name + ('-d' if self.settings.build_type == "Debug" else ''),
                map(
                    lambda name: name + ('' if self.options.shared else '-s'),
                    ['sfml-audio', 'sfml-graphics', 'sfml-network', 'sfml-window', 'sfml-system']
                )
            )
        if not self.settings.os == "Windows":
            self.cpp_info.libs.append("pthread")
            self.cpp_info.libs.append("dl")
