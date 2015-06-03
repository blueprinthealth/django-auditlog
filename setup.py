#!/usr/bin/env python

from setuptools import setup, find_packages
from auditlog import __version__


setup(
    name='django-auditlog',
    version=__version__,
    description='Automated audit/change-tracking for django',
    author='Derek Leverenz',
    author_email='derek@derekleverenz.com',
    license='BSD',
    packages=find_packages(exclude=['testproject']),
    install_requires=['Django>=1.5', 'jsonfield>=0.9.15'],
    zip_safe=True,
)
