#!/usr/bin/env python3
from setuptools import setup

setup(name='bhyve',
      version='0.1',
      description='A tool for managing bhyve VM\'s, '
                  'because libvirt doesn\'t do want I want it to',
      author='Connor Dillon',
      author_email='connor@cdillon.nl',
      license='GPLv3',
      packages=['bhyve'],
      scripts=['scripts/bkeep'],
      install_requires=['PyYAML', 'cmdtool==0.1'],
      zip_safe=False)
