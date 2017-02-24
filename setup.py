#!/usr/bin/env python
# -*- coding: utf-8 -*-
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
from tornado_s3 import __author__, __version__, __license__

setup(
    name='tornado_s3',
    version=__version__,
    description='A Python Interface to the AWS S3',
    author=__author__,
    author_email="steven.lai@liricco.com",
    license=__license__,
    keywords="Facebook Graph API Wrapper Python",
    url='https://github.com/stevenylai/tornado_s3',
    packages=['tornado_s3'],
)
