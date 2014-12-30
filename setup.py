#!/usr/bin/env python3
from setuptools import setup

setup(name='bhyve',
      version='0.2.1',
      description='A tool for managing bhyve VM\'s, '
                  'because libvirt doesn\'t do want I want it to',
      url='https://github.com/ConnorDillon/bhyve',
      author='Connor Dillon',
      author_email='connor@cdillon.nl',
      license='GPLv3',
      packages=['bhyve'],
      scripts=['scripts/bkeep'],
      install_requires=['PyYAML', 'cmdtool==0.2'],
      test_suite='bhyve.tests',
      zip_safe=False)
