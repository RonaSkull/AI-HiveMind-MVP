from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="ai_hivemind",
    version="0.1.0",
    packages=find_packages(include=["mcp", "agents"]),
    install_requires=[
        "redis>=4.5.0",
        "pydantic>=2.0.0",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.3.1",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "fakeredis>=2.10.0",
        ],
    },
    python_requires=">=3.11",
    author="AI HiveMind Team",
    author_email="your.email@example.com",
    description="AI HiveMind - Multi-Agent System for Autonomous NFT Management",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/ai-hivemind",
    classifiers=[
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
