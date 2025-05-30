from setuptools import setup, find_packages

setup(
    name="AutoCatLab",
    version="0.1.0",
    description="Automated Catalyst Laboratory",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    package_data={
        "AutoCatLab.constant": ["*.yaml", "*.json"],
        "AutoCatLab.util": ["*.yaml", "*.json"],
    },
    install_requires=[
        "ase>=3.22.0",
        "pymatgen>=2023.12.18",
        "mp-api>=0.43.0",
        "click>=8.1.7",
        "rich>=13.7.0",
        "sqlalchemy>=2.0.25",
        "mendeleev>=0.14.0",
    ],
    entry_points={
        "console_scripts": [
            "autocatlab=AutoCatLab.main:cli",
        ],
    },
) 