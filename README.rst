pyduofern
=========
.. image:: https://travis-ci.org/gluap/pyduofern.svg?branch=master
    :target: https://travis-ci.org/gluap/pyduofern
.. image:: https://coveralls.io/repos/github/gluap/pyduofern/badge.svg?branch=master
    :target: https://coveralls.io/github/gluap/pyduofern?branch=master

**Disclaimer:** this library is **not** endorsed by the company Rademacher, the manufacturer of home automation products
under the label duofern. The name pyduofern was chosen to indicate the function of the library: communicating with
duofern devices via python.

These are my efforts in porting the `FHEM <http://fhem.de/fhem.html>`_
`Duofern USB-Stick <https://wiki.fhem.de/wiki/DUOFERN>`_ based module to
`Homeassistant <https://home-assistant.io/>`_. As of now the port is rather ugly, but it is usable enough to control
my Duofern blinds. I did not port the Weather-Station related features of the original module -- Mainly because I
do not own the corresponding hardware and have no means to test if it works. I only tested it with the model
*RolloTron Standard DuoFern 14233011 Funk-Gurtwickler Aufputz*.

I do not provide any guarantees for the usability of this software. Use at your own risk.

License::

   python interface for dufoern usb stick
   Copyright (C) 2017 Paul Görgen
   Rough python python translation of the FHEM duofern modules by telekatz
              (also licensed under GPLv2)
   This re-write does not literally contain contain any verbatim lines
   of the original code (given it was translated to another language)
   apart from some comments to facilitate translation of the not-yet
   translated parts of the original software. Modification dates are
   documented as submits to the git repository of this code, currently
   maintained at `https://github.com/gluap/pyduofern.git <https://github.com/gluap/pyduofern.git>`_

   This program is free software; you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation; either version 2 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program; if not, write to the Free Software Foundation,
   Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301  USA

Getting Started
===============

Install via::

     pip3 install pyduofern

or if you want the development version from github::

     pip3 install git+https://github.com/gluap/pyduofern.git@dev

udev configuration
==================
to make your usb stick easy to identify deploy an `udev rules <https://wiki.debian.org/udev>`_ file in
``/etc/udev/rules.d/98-duofern.rules`` or the equivalent of your distribution. The following worked for my
stick::

    SUBSYSTEM=="tty", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6001", SYMLINK+="duofernstick"

Or, if you use several USB-Serial adapters with vendor ``0403`` and product ``6001`` find out the serial number of your
stick (assuming it is currently registered as ``/dev/ttyUSB0```)::

    user@host:~ > udevadm info -a -n /dev/ttyUSB0 | grep '{serial}' | head -n1
    ATTRS{serial}=="WR04ZFP4"

As you can se for me the serial is ``WR04ZFP4``. Use the following udev line (use the serial you found above)::

    SUBSYSTEM=="tty", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6001", ATTRS{serial}=="WR04ZFP4", SYMLINK+="duofernstick"

Once the rule is deployed your stick should show up as ``/dev/duofernstick`` as soon as you plug it in. This
helps avoid confusion if you use other usb-serial devices. Also be warned: The line also makes the stick
accessible to non-root users. But likely on your system you will be the only user anyhow.

Getting Started
===============
To start using your stick you can use the ``duofern_cli.py`` script which should have been installed together
with the pyduofern module. Begin by choosing a 4 hex-digit system code. Ideally write it down, if you forget
it, you will likely have to chose a new system code and reset your devices in order to be able to pair them again.
It is also a security feature which is why no default is provided.

Decide for a system configuration file. By default it will reside as a hidden config file in your home directory in
``~/.duofern.json``. Pass the config file to ``duofern_cli.py`` via the command line option ``--configfile``.
The default has the advantage that you do not always have to pass the config file when using the script. Initialize
the config file with your system code with the following command::

   duofern_cli.py --code <your chosen 4 digit hex code here>
   # or if you prefer your own configfile location
   doufern_cli.py --code <your chosen 4 digit hex code here> --configfile <your config file path>

Now RTFM of the shutter to find out how to start pairing. Set the maximum and minimum positions according to the manual.
If you want to experiment with the shutter first, chose the two positions very near each other. The motors shut down
after a certain maximum runtime and you could exceed that while experimenting if you move the shutters up and down
several times unless the min and max positions are close to each other.

Start out by pairing your first rollershutter::

    duofern_cli.py --pair --pairtime 60

now initiate pairing via the buttons on your shutter. Once a shutter is paired it should show up in your
config file and you can name it. Say the blind that popped up has the ID ``408ea2``, run the following to give it
the name ``kitchen``::

    duofern_cli.py --set_name 408ea2 kitchen
    # you can now try to also have it move up or down:
    duofern_cli.py --up kitchen
    # or try to set the position of a blind (0=down, 100=up)
    duofern_cli.py --position 42 kitchen

Hopefully you now have working command line interface that knows how to move up or down your shutters. But the python
interface can do more, (which I was so far too lazy to expose via the command line):

Indexing paired blinds
----------------------
If you have the system code of your system but lost the list of configured blinds you can use the CLI to refresh
the config file with all paired blinds.::

    # assuming you lost the config file
    duofern_cli.py --code <your code> --refresh --refreshtime 60

will start up the stick and listen for connecting blinds for 60 seconds. It will store all the blinds that were found
in the default config file.a

Usage with Homeassistant
========================
Find an example code for using these blinds with homeassistant in the examples folder


Usage from python
=================
.. code-block:: python

    from pyduofern.duofern_stick import DuofernStick
    import time
    stick = DuofernStick(device="/dev/duofernstick") # by default looks for /dev/duofernstick
    stick_initialize() # do some initialization sequence with the stick
    stick.start() # start the stick in a thread so it keeps communicating with your blinds
    time.sleep(10) # let it settle to be able to talk to your blinds.
    # your code here
    # this uses internal variables of the duofern parser module and likely I will wrap it in
    # the future.

    print(stick.duofern_parser.modules['by_code']['1ff1d3']['position'])

    command("1ff1d3", "up") # open the blind with code 1ff1d3

    stick.command("1ff1d3", "down") # down the blind with code 1ff1d3

    stick.command("1ff1d3", "stop") # stop the blind with code 1ff1d3

    stick.command("1ff1d3", "position", 30) # set position of the blind with code 1ff1d3 to 30%

Look for an indication of possible commands in ``pyduofern/definitions.py``
I just translated them into python and did not explore what might be possible.
It looks like a lot of functionality requires a weather station, but you can just as
easily automate the stuff using your home automation and having it send the up and down
commands instead of buying a weather station.

Changelog
=========

**0.23.5**
- python 3.7 support should enable current hassio version

**0.23.3**
- added ``--position`` to CLI

**0.23.2**
- renamed README.rst and moved version number from `setup.py` to `__init__.py`

**0.23.1**
- fixed references to repository url
- upped version for pypi release

**0.23**
- added recordings and increased coverage of unit tests (no result-based tests yet though -- just checking if every replay runs until the end without hanging)

**0.22**
- Added recording of actions for replay in integration tests
- Improved unit tests
- Enable travis
- Enable coveralls

**0.21.1**
- fixed bug where device IDs containing `cc` would be be messed up when inserting channel number.
