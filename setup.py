"""Setup script for MedLinker AI."""

from setuptools import setup, find_packages

setup(
    name="medlinker-ai",
    version="0.1.0",
    description="Healthcare facility capability extraction and verification pipeline",
    packages=find_packages(),
    python_requires=">=3.11",
    install_requires=[
        "pydantic>=2.0.0,<3.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0,<9.0.0",
        ],
    },
)
