from setuptools import setup, Extension, find_packages
from setuptools.command.build_ext import build_ext
from distutils.errors import CCompilerError, DistutilsExecError, DistutilsPlatformError
from sys import platform
import os
import subprocess


class VerboseBuildExt(build_ext):
    """Build C extensions, but fail with a straightforward exception."""

    def run(self):
        try:
            super().run()
        except DistutilsPlatformError as e:
            raise e

    def build_extension(self, ext):
        try:
            super().build_extension(ext)
        except (CCompilerError, DistutilsExecError, DistutilsPlatformError) as e:
            raise e


def pkgconfig(package):
    flag_map = {"-I": "include_dirs", "-L": "library_dirs", "-l": "libraries"}
    output = subprocess.getoutput(f"pkg-config --cflags --libs {package}")
    if "command not found" in output and platform == "darwin":
        raise ModuleNotFoundError('Please install "pkg-config" using: brew install pkg-config')

    return {
        key: output.strip().split()[2:] for token in output.strip().split() if (key := flag_map.get(token[:2]))
    }



setup(
   name="xian-contracting",
    version="1.0.0",
    description="Python-based smart contract language and interpreter.",
    packages=find_packages(where='src'),  # Find packages in src directory
    package_dir={'': 'src'},  # Root package is in the src directory
    install_requires=[
        "astor==0.8.1",
        "pycodestyle==2.10.0",
        "autopep8==1.5.7",
        "iso8601",
        "h5py",
        "cachetools",
        "loguru",
        "pynacl"
    ],
    url="https://github.com/xian-network/contracting",
    author="Xian",
    author_email="info@xian.org",
    classifiers=[
        "Programming Language :: Python :: 3.11",
    ],
    zip_safe=True,
    include_package_data=True,
    ext_modules=[
        Extension(
            "contracting.execution.metering.tracer",
            ["src/contracting/execution/metering/tracer.c"]
        ),
    ],
    cmdclass={
        "build_ext": VerboseBuildExt,
    },
)
