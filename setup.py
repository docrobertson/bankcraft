from setuptools import setup, find_packages

setup(
    name="bankcraft",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        # your dependencies here
        "mesa<4",
        "jupyter",
        "numpy",
        "pandas",
        "matplotlib",
        "seaborn",
        "scipy",
        "scikit-learn",
        "scikit-learn",
    ],
) 