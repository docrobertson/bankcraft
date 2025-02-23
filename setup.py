from setuptools import setup, find_packages

setup(
    name="bankcraft",
    version="0.1",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
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