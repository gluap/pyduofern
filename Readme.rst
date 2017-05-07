pyduofern
=========

These are my efforts in porting the `FHEM <http://fhem.de/fhem.html>`_
`Duofern USB-Stick <https://wiki.fhem.de/wiki/DUOFERN>`_ based module to
`Homeassistant <https://home-assistant.io/>`_. As of now the port is rather ugly, but it is usable enough to control
my Duofern blinds. I did not port the Weather-Station related features of the original module -- Mainly because I
do not own the corresponding hardware and have no means to test if it works.

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
   maintained at `https://bitbucket.org/gluap/pyduofern.git <https://bitbucket.org/gluap/pyduofern.git>`_

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

To install the python module run ``python setup.py install`` if you downloaded
the sources already or use the convenience mechanism and run::

     pip install git+https://bitbucket.org/gluap/pyduofern.git

udev configuration
==================
to make your usb stick easily to identify deploy an `udev rules <https://wiki.debian.org/udev>`_ file in
``/etc/udev/rules.d/98-duofern.rules`` or the equivalent of your distribution. The following worked for my
stick::

    SUBSYSTEM=="tty", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6001", ATTRS{serial}=="WR04ZFP4", SYMLINK+="duofernstick"

Once the rule is deployed your stick should show up as ``/dev/duofernstick`` as soon as you plug it in. This
helps avoid confusion if you use other usb-serial devices.

Getting
=====
To start using your stick you can use the ``duofern_cli.py`` script which should have been installed together
with the pyduofern module. Begin by chosing a 4 hex-digit system code. Ideally write it down, if you forget
it, you will likely have to chose a new system code and reset your devices in order to be able to pair them again.



