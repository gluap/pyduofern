# !/usr/bin/env python3
# coding=utf-8
#   python interface for dufoern usb stick
#   Copyright (C) 2017 Paul Görgen
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; in version 2 of the license
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program; if not, write to the Free Software Foundation,
#   Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301  USA


import argparse
import logging
import re
import time

from pyduofern.duofern_stick import DuofernStick

parser = argparse.ArgumentParser(epilog="use at your own risk")

parser.add_argument('--configfile', help='location of system config file', default=None, metavar="CONFIGFILE")

parser.add_argument('--code', help='set 4-digit hex code for the system (warning, always use same code for once-paired '
                                   'devices) best chose something on the first run and write it down.',
                    default=None, metavar="SYSTEMCODE")

parser.add_argument('--device',
                    help='path to serial port created by duofern stick, defaults to first found serial port, typically '
                         'something like /dev/ttyUSB0 or /dev/duofernstick if you use the provided udev rules file',
                    default=None)

parser.add_argument('--pair', action='store_true',
                    help='Stick will wait for pairing for {} seconds. Afterwards look in the config file for the paired '
                         'device name or call this program again to list the newly found device. If devices that were '
                         'paired with this SYSTEMCODE are found while waiting for pairing, these are also added to'
                         'CONFIGFILE',
                    default=False)
parser.add_argument('--pairtime', help='time to wait for pairing requests', metavar="SECONDS", default=60, type=int)

parser.add_argument('--refresh', action='store_true',
                    help='just sit and listen for devices that were already paired with the current system code but '
                         'were lost from the config file', default=False)
parser.add_argument('--refreshtime', help='time to spend refreshing',
                    metavar="SECONDS", default=60, type=int)

parser.add_argument('--set_name', help='Set name for a device.', nargs=2, default=None,
                    metavar=("DEVICE_ID", "DEVICE_NAME"))

parser.add_argument('--debug', help='enable verbose logging', action='store_true', default=False)

parser.add_argument('--up', help='pull up the selected rollershutter / blinds', metavar="NAME", nargs='+', default=None)

args = parser.parse_args()

if __name__ == "__main__":
    if args.debug:
        logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
    else:
        logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

    if args.code is not None:
        assert len(args.code) == 4, "System code must be a 4 digit hex code"
        try:
            bytearray.fromhex(args.code)
        except:
            print("System code must be a 4 digit hex code")
            exit(1)

    stick = DuofernStick(device=args.device, system_code=args.code, config_file_json=args.configfile)

    if args.set_name is not None:
        assert len(args.set_name[0]) == 6 and re.match("^[0-9a-f]+$", args.set_name, re.IGNORECASE), "id for renaming" \
                                                                                                     " must be a valid 6 digit hex ID not {}".format(
            args.set_name[0])
        stick.set_name(args.set_name[0], args.set_name[1])
        stick._dump_config()

    print("The following devices are configured:")

    print("\n".join(
        ["id: {:6}    name: {}".format(device['id'], device['name']) for device in stick.config['devices']]))

    if args.pair:
        print("entering pairing mode")
        stick._initialize()
        stick.start()
        stick.pair(timeout=args.pairtime)
        time.sleep(args.pairtime + 0.5)
        print("""""")

    if args.refresh:
        stick._initialize()
        stick.start()
        time.sleep(args.refreshtime + 0.5)
        stick.sync_devices()

    if args.up:
        ids = [device['id'] for device in stick.config['devices'] if device['name'] in args.up]
    stick.stop()
    time.sleep(1)
    stick.join()
