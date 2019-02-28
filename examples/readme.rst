Examples
========

Homeassistant
-------------

To use ``pyduofern`` within `Homeassistant <https://home-assistant.io/>`_, add the ``custom_components`` directory to
``~/.homeassistant/`` directory and enable it by adding the following to your ``configuration.yaml``::

    duofern:
       # serial_port defaults to
       # /dev/serial/by-id/usb-Rademacher_DuoFern_USB-Stick_WR04ZFP4-if00-port0
       # which should work on most linuxes
       # serial_port: /dev/ttyUSB0
       # code defaults to 0000 and should definitely be chosen randomly
       # (4 hex digits required)
       code: deda

There are two services you can call via the service interface:

``duofern.start_pairing`` starts the pairing mode for a given number of seconds.
``duofern.sync_devices`` will force-sync any newly discovered devices.

Please use the renaming feature in the homeassistant GUI to arrive at human readable
names for your devices.