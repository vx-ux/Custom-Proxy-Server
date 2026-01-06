from setuptools import setup, find_packages

setup(
    name="proxy-server",
    version="1.0.0",
    description="Async HTTP/HTTPS Forward Proxy Server with caching and domain filtering",
    author="Vansh",
    python_requires=">=3.8",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    entry_points={
        "console_scripts": [
            "proxy-server=proxy.proxy:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
