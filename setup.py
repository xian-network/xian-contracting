from setuptools import setup, find_packages

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
        "pynacl",
        "psutil",
    ],
    url="https://github.com/xian-network/contracting",
    author="Xian",
    author_email="info@xian.org",
    classifiers=[
        "Programming Language :: Python :: 3.11",
    ],
    zip_safe=True,
    include_package_data=True,
    python_requires='~=3.11.0',
)
