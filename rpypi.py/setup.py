#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

import versioneer
from setuptools import find_packages, setup

with open('../README.md') as readme_file:
    readme = readme_file.read()

requirements = [
    'versioneer>=0.18',
]

setup_requirements = ['pytest-runner', ]

test_requirements = [
    'pytest>=5.1.2',
    'pytest-cov>=2.7.1',
]

setup(
    name='rpypi',
    keywords='',
    author="David Golembiowski",
    author_email='dmgolembiowski<\/\/~at]]]]geemayl.com',
    python_requires='>=3.9.*',
    license='GNU General Public License v3',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Programming Language :: Rust',
        'Topic :: Software Development',

    ],
    description='if you are reading this on Pypi, i have failed you',
    install_requires=requirements,
    long_description=readme,
    include_package_data=True,
#    packages=find_packages(include=['dicom_anon']),
    setup_requires=setup_requirements,
#    test_suite='tests',
#    tests_require=test_requirements,
#    url='',
    zip_safe=False,
    version=0.0.0,
    cmdclass=None,
)
