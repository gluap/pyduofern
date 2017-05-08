Examples
========

Homeassistant
-------------

To use ``pyduofern`` within `Homeassistant <https://home-assistant.io/>`_, add the custom_components directory to
``~/.homeassistant/`` directory and enable it by adding the following lines to the config file::

    cover:
      - platform: duofern
        serial_port: # optional, defaults to "/dev/duofernstick"
        config_file: # optional, defaults to ~/.dufoern.json
        code: asdf # optional if correctly defined in .duofern.json