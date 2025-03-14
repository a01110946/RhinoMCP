"""RhinoMCP package setup script."""
from setuptools import setup, find_packages

setup(
    name="rhinomcp",
    version="0.1.0",
    description="Connect Rhino3D to Claude AI via the Model Context Protocol",
    author="Fernando Maytorena",
    author_email="",
    url="https://github.com/FernandoMaytorena/RhinoMCP",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.10",
    install_requires=[
        "websockets>=11.0.0",
        "typing-extensions>=4.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-mock>=3.10.0",
            "pytest-asyncio>=0.21.0",
            "ruff>=0.0.270",
            "mypy>=1.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "rhinomcp=rhino_mcp.mcp_server:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
    ],
)
