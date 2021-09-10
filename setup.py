from setuptools import setup


version = "0.1.0"


setup(
    name="smpl_tools",
    packages=["smpl_tools"],
    version=version,
    description="Sample Toolset for working with sample CDs and misc other tasks.",
    author="Counselor Chip",
    install_requires=["future", "numpy"],
    setup_requires=[
        "numpy"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
    ],
)