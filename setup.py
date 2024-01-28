# coding=utf-8
from setuptools import setup

from pyduofern import __version__ as version

test_deps = [
    'tox', 'pytest<8', 'pytest-asyncio'
],

extras = {
    'test': test_deps,
}

setup(name='pyduofern',
      version=version,
      description='Library for controlling Rademacher DuoFern actors using python. Requires the Rademacher'
                  'Duofern USB Stick Art.-Nr.: 70000093',
      classifiers=[
          'Development Status :: 3 - Alpha',
          'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
          'Programming Language :: Python :: 3.4',
      ],

      url='https://github.com/gluap/pyduofern',
      author='Paul Görgen',
      author_email='pypi@pgoergen.de',
      license='GPL-2.0',

      packages=['pyduofern'],

      install_requires=[
          'pyserial', 'pyserial-asyncio'
      ],

      zip_safe=False,
      include_package_data=False,

      tests_require=test_deps,
      extras_require=extras,

      scripts=["scripts/duofern_cli.py"],

      long_description=open('README.rst', 'r').read()
      )
