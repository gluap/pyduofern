Examples
========
This Documentation will migrate into `<https://github.com/gluap/pyduofern-hacs>`_
Setup with Homeassistant OS (using HACS)
----------------------------------------
Use HACS and follow the manual on `<https://github.com/gluap/pyduofern-hacs>`_

Setup with vanilla homeassistant (no hassio)
--------------------------------------------
To use ``pyduofern`` within `Homeassistant <https://home-assistant.io/>`_, add the ``custom_components`` from `<https://github.com/gluap/pyduofern-hacs>`_  from the examples  to
``~/.homeassistant/`` directory and enable it by adding the following to your ``configuration.yaml``::

    duofern:
       # (4 hex digits as code required, last 4 digits if migrating from FHEM)
       code: deda
       # Optional options, comment in if required:
       # serial_port: /dev/ttyUSB0
       #   # serial_port defaults to
       #   # /dev/serial/by-id/usb-Rademacher_DuoFern_USB-Stick_WR04ZFP4-if00-port0
       #   # which should work on most linuxes
       # config_file: ~/duofern.json
       #   # config_file defaults to duofern.json in homeassistant folder (assuming custom_component is used)

Usage
-----
There are two services you can call via the service interface:

``duofern.start_pairing`` starts the pairing mode for a given number of seconds.

.. image:: ./pairing.png

``duofern.sync_devices`` will force-sync any newly discovered devices.

.. image:: ./sync_devices.png

Please use the renaming feature in the homeassistant GUI to arrive at human readable
names for your devices.

.. image:: ./renaming.png
