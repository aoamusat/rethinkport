#!/usr/bin/env python3
"""
Setup script for RethinkDB to MySQL Migrator
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [
        line.strip() for line in fh if line.strip() and not line.startswith("#")
    ]

setup(
    name="rethinkport",
    version="1.0.0",
    author="RethinkPort Contributors",
    author_email="your-email@example.com",
    description="Port your RethinkDB data to MySQL",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/aoamusat/rethinkport",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Database",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "rethinkport=rethinkdb_mysql_migrator.cli:main",
        ],
    },
    keywords="rethinkdb mysql migration database port converter rethinkport",
    project_urls={
        "Bug Reports": "https://github.com/aoamusat/rethinkport/issues",
        "Source": "https://github.com/aoamusat/rethinkport",
        "Documentation": "https://github.com/aoamusat/rethinkport#readme",
    },
)
