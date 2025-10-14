from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ntfs-file-recovery",
    version="1.0.0",
    author="NTFS Recovery Team",
    description="A comprehensive NTFS file recovery tool using PyTSK3",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/ntfs-file-recovery",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: System :: Filesystems",
        "Topic :: Security :: Forensics",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pytsk3>=20231007",
        "tqdm>=4.65.0",
        "colorama>=0.4.6",
        "tabulate>=0.9.0",
    ],
    entry_points={
        "console_scripts": [
            "ntfs-recovery=src.main:main",
        ],
    },
)

