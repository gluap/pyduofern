# coding=utf-8
from setuptools import setup

setup(name='pyduofern',
      version='0.21.1',
      description='Library for controlling Rademacher DuoFern actors using python. Requires the Rademacher'
                  'Duofern USB Stick Art.-Nr.: 70000093',
      classifiers=[
          'Development Status :: 3 - Alpha',
          'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
          'Programming Language :: Python :: 3.4',
      ],

      url='https://bitbucket.org/gluap/pyduofern',
      author='Paul Görgen',
      author_email='pypi@pgoergen.de',
      license='GPL-2.0',

      packages=['pyduofern'],

      install_requires=[
          'pyserial', 'pyserial-asyncio'
      ],

      zip_safe=False,
      include_package_data=False,

      tests_require=[
          'tox', 'pytest', 'pytest-asyncio'
      ],

      scripts=["scripts/duofern_cli.py"]
      )
