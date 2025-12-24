# Copyright 2024 Lead Engine
# Licensed under the Apache License, Version 2.0

from setuptools import setup, find_packages

with open("README.md") as f:
    readme = f.read()

requirements = [
    "requests>=2.20.0,<3.0",
]

dev_requirements = [
    "pytest>=7.0.0",
    "responses>=0.20.0",
]

setup(
    name="lead-engine",
    version="1.0.0",
    description="Production-ready lead generation from Google Places API with email enrichment",
    long_description=readme,
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="your@email.com",
    url="https://github.com/yourusername/lead-engine",
    packages=find_packages(exclude=["tests", "tests.*", "archive", "archive.*"]),
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "lead-engine=lead_engine.__main__:main",
        ],
    },
    license="Apache 2.0",
    platforms="Posix; MacOS X; Windows",
    install_requires=requirements,
    extras_require={
        "dev": dev_requirements,
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet",
        "Topic :: Office/Business",
    ],
    python_requires=">=3.8",
)
