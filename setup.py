"""Setup configuration for deburger package."""

from setuptools import setup, find_packages
from pathlib import Path

readme = Path("README.md").read_text(encoding="utf-8")

setup(
    name="deburger",
    version="0.2.0",
    description="AI Code Quality Guardian - Monitor AI-generated code quality and requirement alignment",
    long_description=readme,
    long_description_content_type="text/markdown",
    author="Sahil Nayak",
    author_email="sahilnayak2056@gmail.com",
    url="https://github.com/sahilnyk/deburger",
    license="MIT",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.9",
    install_requires=[
        "typer>=0.9.0",
        "rich>=13.7.0",
        "PyYAML>=6.0.1",
    ],
    extras_require={
        "llm": ["openai>=1.6.0", "anthropic>=0.18.0"],
        "dev": ["pytest>=7.4.0", "pytest-cov>=4.1.0", "mypy>=1.8.0", "ruff>=0.1.0"],
    },
    entry_points={
        "console_scripts": [
            "deburger=deburger.cli.main:app",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Software Development :: Testing",
    ],
    keywords="ai code-quality security monitoring testing",
)
