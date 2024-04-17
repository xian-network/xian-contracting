from setuptools import setup, Extension, find_packages
from setuptools.command.build_ext import build_ext
from distutils.errors import CCompilerError, DistutilsExecError, DistutilsPlatformError
from sys import platform
import sys, subprocess, pathlib

major = 0

__version__ = "2.0.10"

requirements = [
    "astor==0.8.1",
    "pycodestyle==2.10.0",
    "autopep8==1.5.7",
    "motor==2.5.1",
    "iso8601",
    "h5py"
]

ext_errors = (CCompilerError, DistutilsExecError, DistutilsPlatformError)


class BuildFailed(Exception):
    def __init__(self):
        self.cause = sys.exc_info()[1]  # work around py 2/3 different syntax


class ve_build_ext(build_ext):
    """Build C extensions, but fail with a straightforward exception."""

    def run(self):
        """Wrap `run` with `BuildFailed`."""
        try:
            build_ext.run(self)
        except DistutilsPlatformError:
            raise BuildFailed()

    def build_extension(self, ext):
        """Wrap `build_extension` with `BuildFailed`."""
        try:
            # Uncomment to test compile failure handling:
            #   raise errors.CCompilerError("OOPS")
            build_ext.build_extension(self, ext)
        except ext_errors:
            raise BuildFailed()
        except ValueError as err:
            # this can happen on Windows 64 bit, see Python issue 7511
            if "'path'" in str(err):  # works with both py 2/3
                raise BuildFailed()
            raise


def pkgconfig(package):
    flag_map = {"-I": "include_dirs", "-L": "library_dirs", "-l": "libraries"}
    res = {}

    if platform == "linux" or platform == "linux2":
        output = subprocess.getoutput("pkg-config --cflags --libs {}".format(package))
        for token in output.strip().split():
            key = flag_map.get(token[:2])
            if key:
                res.setdefault(key, []).append(token[2:])

    elif platform == "darwin":
        output = subprocess.getoutput("pkg-config --version")
        if "command not found" in output:
            raise ModuleNotFoundError(
                'Install "pkg-config" using brew. "brew install pkg-config"'
            )

        output = subprocess.getoutput("pkg-config --cflags --libs {}".format(package))
        for token in output.strip().split():
            key = flag_map.get(token[:2])
            if key:
                res.setdefault(key, []).append(token[2:])

    elif platform == "win32":
        try:
            output = subprocess.getoutput("pkg-config --cflags --libs {}".format(package))
            for token in output.strip().split():
                key = flag_map.get(token[:2])
                if key:
                    res.setdefault(key, []).append(token[2:])
        except Exception:
            # Fallback if pkg-config is not installed
            raise NotImplementedError("pkg-config is not configured for Windows. Install or configure pkg-config.")

    # Convert values to strings
    res = {key: [str(value) for value in values] for key, values in res.items()}
    return res


setup(
    name="contracting",
    version=__version__,
    description="Python-based smart contract language and interpreter.",
    packages=find_packages(),
    install_requires=requirements,
    url="https://github.com/Lamden/contracting",
    author="Lamden",
    author_email="team@lamden.io",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    zip_safe=True,
    include_package_data=True,
    ext_modules=[
        Extension(
            "contracting.execution.metering.tracer",
            sources=["contracting/execution/metering/tracer.c"],
        ),
    ],
    cmdclass={
        "build_ext": ve_build_ext,
    },
)
