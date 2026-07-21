from setuptools import setup, find_packages

setup(
    name="scandium-dataset",
    version="0.0.0",
    description="Curated computational materials dataset for solid-state battery discovery",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/ScandiumLabs-in/Scandium-Dataset",
    author="Scandium Labs",
    license="Multiple (see LICENSE)",
    packages=find_packages(include=["api", "api.*"]),
    python_requires=">=3.10",
    install_requires=[
        "numpy>=1.24",
        "scipy>=1.10",
        "pymatgen>=2024.0",
        "ase>=3.22",
        "spglib>=2.0",
        "torch>=2.0",
    ],
    extras_require={
        "benchmark": ["scikit-learn>=1.3", "matplotlib>=3.7"],
        "dev": ["pytest>=7", "pytest-cov>=4"],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "License :: Other/Proprietary License",
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering :: Chemistry",
        "Topic :: Scientific/Engineering :: Physics",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
)
