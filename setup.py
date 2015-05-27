import os

from codecs import open

import hgdistver

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()
    
pampas_core_path = os.path.join(here, 'pampas', 'core')

try:
    version = hgdistver.get_version()
    
except AssertionError:
    version = hgdistver.get_version(guess_next=False)
    
setup(
    name='xdh-config',
    
    version=version.split('+')[0],
    
    description='A simple library providing the config module, which contains read-only, lazily-computed objects useful for configuration settings.',
    
    long_description=long_description,
    
    author='Cliff Hill',
    author_email='xlorep@darkhelm.org',
    
    url='https://github.com/xlorepdarkhelm/config',
    download_url = 'https://github.com/xlorepdarkhelm/config/archive/master.zip',
    
    license='MIT',
    
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    
    keywords='config xdh',
    
    packages=find_packages(exclude=['test*']),
)
