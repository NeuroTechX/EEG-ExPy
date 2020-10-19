#!/usr/bin/env python

from setuptools import setup, find_packages

with open("README.rst", "r") as fh:
    long_description = fh.read()

with open('requirements.txt', 'r') as fp:
    install_requires = fp.read().splitlines()

setup(
    name="eeg-notebooks", 
    version="0.2",
    author="John David Griffiths",
    author_email="j.davidgriffiths@gmail.com",
    description='python library for eeg cognitive neuroscience experiments',
    keywords='eeg, cognitive neuroscience, experiments, evoked response, auditory, visual',
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires = install_requires,
    url='https://github.com/NeuroTechX/eeg-notebooks',
    license="BSD (3-clause",
    entry_points={"console_scripts": ["eegnb=eegnb.cli.__main__:main"]},
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
