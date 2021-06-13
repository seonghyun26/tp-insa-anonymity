#!/usr/bin/env python3

import setuptools
from distutils.core import setup


with open('README.md', encoding='utf-8') as readme_file:
    readme = readme_file.read()

setup(
    name="tp-insa-anonymity",
    version='1.0.0',
    description='',
    long_description=readme,
    long_description_content_type='text/markdown',
    author='abetraou',
    packages=['anonymity'],
    install_requires=['numpy==1.20.2', 'pandas==1.2.4', 'python-dp', 'matplotlib'],
    extras_require={
	"data": ['requests', 'openpyxl'],
        "notebook": ['jupyter', 'seaborn'],
        "docs": ['sphinx', 'sphinx-rtd-theme', 'numpydoc']
    }
)
