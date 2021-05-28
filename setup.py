#!/usr/bin/env python3

import setuptools
from distutils.core import setup


with open('README.md', encoding='utf-8') as readme_file:
    readme = readme_file.read()

setup(
    name="python_db_lecture",
    version='1.0.0',
    description='',
    long_description=readme,
    long_description_content_type='text/markdown',
    author='abetraou',
    packages=['python_db_lecture'],
    install_requires=['numpy==1.20.2', 'pandas==1.2.4', 'requests', 'openpyxl'],
    extras_require={
        "notebook": ['jupyter', 'matplotlib', 'seaborn']
    }
)
