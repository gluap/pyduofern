pyduofern
=========

These are my efforts in porting the `FHEM <http://fhem.de/fhem.html>`_
`Duofern USB-Stick <https://wiki.fhem.de/wiki/DUOFERN>`_ based module to
`Homeassistant <https://home-assistant.io/>`_.

I prefer Python over perl and would like to use my Duofern blinds with
Homeassistant.


Installation:
=============

To install the python module run ``python setup.py install`` if you downloaded
the sources already or use the convenience mechanism and run::

     pip install git+https://bitbucket.org/gluap/pyduofern.git

udev configuration
==================
to make your usb stick easily identifiable deploy an `udev rules <https://wiki.debian.org/udev>`_ file in
``/etc/udev/rules.d/98-duofern.rules`` or the equivalent of your distribution. The following worked for my
stick::

    SUBSYSTEM=="tty", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6001", ATTRS{serial}=="WR04ZFP4", SYMLINK+="duofernstick"

Once the rule is deployed your stick should show up as ``/dev/duofernstick`` as soon as you plug it in. This
helps avoid confusion if you use other usb-serial devices.

Usage:
======
To first running your stick you can use the duofern_cli.py script which should have been installed together
with the pyduofern module. Begin by chosing a s