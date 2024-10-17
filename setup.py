from setuptools import setup, find_packages

setup(
    name="slic3r_display",
    version="0.1.0",
    description="Module to provide easy converter from 3D data to 3D Slic3r representations",
    author="Vinzent Rittel",
    author_email="mail@vinzentrittel.de",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.9",
)
