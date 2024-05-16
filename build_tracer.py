from distutils.core import setup, Extension
from distutils.command.build_ext import build_ext

tracer_extension = Extension(
    'contracting.execution.metering.tracer',
    sources=['contracting/execution/metering/tracer.c']
)

setup(
    name='contracting',
    cmdclass={'build_ext': build_ext},
    ext_modules=[tracer_extension],
)
