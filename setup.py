#!/usr/bin/env python
from setuptools import setup, find_packages
import os

def read(fname):
	return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(name='costa-ci',
	author='Larry Cai',
    version = "0.0.4",
	author_email='larry.caiyu@gmail.com',
	url='https://github.com/larrycai/costa-ci',
	license='MIT',
	packages=find_packages(),
	description='CI relateds scripts using openstack',
	long_description=read('README.rst'),
	classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: Freely Distributable',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Topic :: Software Development :: Testing',
	    ],
	)

