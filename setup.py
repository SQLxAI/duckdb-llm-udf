"""
Setup script for duckdb_llm_udf
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="duckdb_llm_udf",
    version="0.1.1", 
    author="Your Name",
    author_email="your.email@example.com",
    description="A DuckDB extension for natural language querying using LLMs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/duckdb_llm_udf",
    package_dir={"" : "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "duckdb>=0.8.0",
        "python-dotenv>=0.19.0",
        "numpy>=1.21.0",
    ],
    extras_require={
        "openai": ["openai>=1.0.0"],
        "anthropic": ["anthropic>=0.5.0"],
        "all": ["openai>=1.0.0", "anthropic>=0.5.0"],
    },
)
