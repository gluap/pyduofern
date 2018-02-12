Examples
========

Homeassistant
-------------

To use ``pyduofern`` within `Homeassistant <https://home-assistant.io/>`_, add the custom_components directory to
``~/.homeassistant/`` directory and enable it by adding the following lines to the config file. Use the same
values for the light and cover platforms.

If you have other `light` or `cover` platforms in place please just add the lines starting with `- platform` to the
respective sections.::

    cover:
      - platform: duofern
        serial_port: # optional, defaults to first detected tty. You probably want to adapt this, for example
                     # to /dev/duofernstick after adapting your udev config
        config_file: # optional, defaults to ~/.dufoern.json
        code: beef # 4 hex digits, optional if correctly defined in .duofern.json
    # light is basically a duplicate... sorry
    light:
      - platform: duofern
        serial_port: # see above
        config_file: # see above
        code: beef # see above