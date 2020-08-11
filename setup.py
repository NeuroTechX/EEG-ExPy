#!/usr/bin/env python

from setuptools import setup, find_packages
import versioneer 

setup(name='eeg-notebooks', #version=versioneer.get_version(),
      description='python library for eeg cognitive neuroscience experiments',
      long_description='python library for eeg cognitive neuroscience experiments',
      keywords='eeg, cognitive neuroscience, experiments, evoked response, auditory, visual',
      author='John David Griffiths',
      author_email='j.davidgriffiths@gmail.com',
      url='https://github.com/NeuroTechX/eeg-notebooks',
      packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]), 
      install_requires=['numpy',  'setuptools'],
      classifiers=[
          'Intended Audience :: Science/Research',
          'Programming Language :: Python',
          'Topic :: Software Development',
          'Topic :: Scientific/Engineering',
          'Operating System :: Microsoft :: Windows',
          'Operating System :: POSIX',
          'Operating System :: Unix',
          'Operating System :: MacOS',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3.6',
      ],
      entry_points={
          "console_scripts": [
              "eegnb=eegnb.__main__:main",
          ]
      },
      #cmdclass=versioneer.get_cmdclass()
      )


