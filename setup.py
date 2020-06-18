import os
from setuptools import setup

setup(
    name="bathymetry",
    version="0.0.1",
    packages=["bathymetry"],
    url="https://github.com/brendan-ward/bathymetry",
    license="MIT",
    author="Brendan C. Ward",
    author_email="bcward@astutespruce.com",
    description="Processing tools for creating bathymetry tiles for web maps",
    long_description_content_type="text/markdown",
    long_description=open("README.md").read(),
    install_requires=[],  # TODO
    include_package_data=True,
)
