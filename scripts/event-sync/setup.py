#!/usr/bin/env python3
"""
Setup script for Will's Pub to Gancio Sync
"""

from setuptools import find_packages, setup

setup(
    name="willspub-gancio-sync",
    version="1.0.0",
    description="Sync events from Will's Pub to Gancio",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Orlando Punk Shows",
    url="https://orlandopunx.com",
    py_modules=[
        "willspub_manual_import",
        "willspub_selenium_sync",
        "willspub_to_gancio_final_working",
    ],
    install_requires=[
        "requests>=2.25.1",
        "beautifulsoup4>=4.9.3",
    ],
    extras_require={
        "selenium": ["selenium>=4.0.0"],
    },
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    entry_points={
        "console_scripts": [
            "willspub-import=willspub_manual_import:main",
        ],
    },
)
