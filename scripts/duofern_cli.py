#!/usr/bin/python3
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
from cmd import Cmd

from pyduofern.duofern_stick import DuofernStickThreaded


parser = argparse.ArgumentParser(epilog="use at your own risk")

parser.add_argument('--configfile', help='location of system config file (if omitted the default config file will be used)', default=None, metavar="CONFIGFILE")

parser.add_argument('--code', help='set 4-digit hex code for the system (warning, always use same code for once-paired '
                                   'devices) best chose something on the first run and write it down.',
                    default=None, metavar="SYSTEMCODE")

parser.add_argument('--device',
                    help='path to serial port created by duofern stick, defaults to first found serial port, typically '
                         'something like /dev/ttyUSB0 or /dev/serial/by-id/... or /dev/duofernstick if you use the provided udev rules file',
                    default=None)

parser.add_argument('--pair', action='store_true',
                    help='Stick will wait for pairing for {} seconds. Afterwards look in the config file for the paired '
                         'device name or call this program again to list the newly found device. If devices that were '
                         'paired with this SYSTEMCODE are found while waiting for pairing, these are also added to'
                         'CONFIGFILE',
                    default=False)

parser.add_argument('--show_paired', action='store_true',
                    help='Show known and configured Duofern devices',
                    default=False)

parser.add_argument('--unpair', action='store_true',
                    help='Stick will wait for pairing for {} seconds. Afterwards look in the config file for the paired '
                         'device name or call this program again to list the newly found device. If devices that were '
                         'paired with this SYSTEMCODE are found while waiting for pairing, these are also added to'
                         'CONFIGFILE',
                    default=False)

parser.add_argument('--remote',
                    help='Pair by code. Added devices are also added to CONFIGFILE',
                    metavar='DEVICE_ID', default=None)

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
parser.add_argument('--down', help='roll down the selected rollershutter / blinds', metavar="NAME", nargs='+', default=None)
parser.add_argument('--stop', help='stop the selected rollershutter / blinds', metavar="NAME", nargs='+', default=None)

parser.add_argument('--on', help='switch on (for "Steckdosenaktor")', metavar="NAME", nargs='+', default=None)
parser.add_argument('--off', help='switch off (for "Steckdosenaktor")', metavar="NAME", nargs='+',
                    default=None)
parser.add_argument('--stairwell_on', help='switch on stairwell (for "Steckdosenaktor")', metavar="NAME", nargs='+',
                    default=None)
parser.add_argument('--stairwell_off', help='switch on stairwell (for "Steckdosenaktor")', metavar="NAME", nargs='+',
                    default=None)
parser.add_argument('--position', help='move shutter NAME to position POSITION', metavar=('POSITION', 'NAME'), nargs=2,
                    default=None, type=str)



if __name__ == "__main__":
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(format='    %(asctime)s: %(message)s', level=logging.DEBUG)
    else:
        logging.basicConfig(format='    %(asctime)s: %(message)s', level=logging.INFO)

    if args.code is not None:
        assert len(args.code) == 4, "System code must be a 4 digit hex code"
        try:
            bytearray.fromhex(args.code)
        except:
            print("System code must be a 4 digit hex code")
            exit(1)

    stick = DuofernStickThreaded(serial_port=args.device, system_code=args.code, config_file_json=args.configfile)

    if args.set_name is not None:
        assert len(args.set_name[0]) == 6 and re.match("^[0-9a-f]+$", args.set_name[0], re.IGNORECASE), \
            "id for renaming must be a valid 6 digit hex ID not {}".format(args.set_name[0])
        stick.set_name(args.set_name[0], args.set_name[1])
        stick.sync_devices()

    if args.show_paired:
        print("\nThe following devices are configured:\n")
        print("\n".join(["id: {:6}    name: {}".format(device['id'], device['name']) for device in stick.config['devices']]))
        print("\n")

    if args.pair:
        print("entering pairing mode")
        stick._initialize()
        stick.start()
        stick.pair(timeout=args.pairtime)
        time.sleep(args.pairtime + 0.5)
        stick.sync_devices()
        print("""""")

    if args.unpair:
        print("entering pairing mode")
        stick._initialize()
        stick.start()
        stick.unpair(timeout=args.pairtime)
        time.sleep(args.pairtime + 0.5)
        stick.sync_devices()
        print("""""")

    if args.remote:
        print("entering remote pairing mode")
        stick._initialize()
        stick.start()
        stick.pair(timeout=args.pairtime)
        stick.remote(code=args.remote, timeout=args.pairtime)
        time.sleep(args.pairtime + 0.5)
        stick.sync_devices()
        print("""""")

    if args.refresh:
        stick._initialize()
        stick.start()
        time.sleep(args.refreshtime + 0.5)
        stick.sync_devices()

    if args.up:
        stick._initialize()
        stick.start()
        ids = [device['id'] for device in stick.config['devices'] if device['name'] in args.up]
        for blind_id in ids:
            stick.command(blind_id, "up")
            time.sleep(1)

    if args.down:
        stick._initialize()
        stick.start()
        ids = [device['id'] for device in stick.config['devices'] if device['name'] in args.down]
        for blind_id in ids:
            stick.command(blind_id, "down")
            time.sleep(1)
    
    if args.stop:
        stick._initialize()
        stick.start()
        ids = [device['id'] for device in stick.config['devices'] if device['name'] in args.stop]
        for blind_id in ids:
            stick.command(blind_id, "stop")
            time.sleep(1)

    if args.on:
        stick._initialize()
        stick.start()
        time.sleep(1)
        ids = [device['id'] for device in stick.config['devices'] if device['name'] in args.on]
        for blind_id in ids:
            stick.command(blind_id, "on")
            time.sleep(2)

    if args.off:
        stick._initialize()
        stick.start()
        time.sleep(1)
        ids = [device['id'] for device in stick.config['devices'] if device['name'] in args.off]
        for blind_id in ids:
            stick.command(blind_id, "off")
            time.sleep(2)

    if args.stairwell_on:
        stick._initialize()
        stick.start()
        time.sleep(1)
        ids = [device['id'] for device in stick.config['devices'] if device['name'] in args.stairwell_on]
        for blind_id in ids:
            stick.command(blind_id, "stairwellTime", 10)
            time.sleep(0.5)
            stick.command(blind_id, "stairwellFunction", "on")
            time.sleep(0.5)
            stick.command(blind_id, "on")
            time.sleep(2)

    if args.stairwell_off:
        stick._initialize()
        stick.start()
        time.sleep(1)
        ids = [device['id'] for device in stick.config['devices'] if device['name'] in args.stairwell_off]
        for blind_id in ids:
            stick.command(blind_id, "stairwellFunction", "off")
            time.sleep(0.5)
            stick.command(blind_id, "on")
            time.sleep(2)

    if args.position is not None:
        stick._initialize()
        stick.start()
        ids = [device['id'] for device in stick.config['devices'] if device['name'] in args.position[1:]]
        for blind_id in ids:
            stick.command(blind_id, "position", 100 - int(args.position[0]))
            time.sleep(1)

    stick.stop()
    time.sleep(1)
    try:
        stick.join()
    except RuntimeError:
        pass
