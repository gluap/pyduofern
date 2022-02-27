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


def splitargs(func):
    def wrapper(*args, **kwargs):
        func(args[0], args[1].split(" "))

    return wrapper


def ids_for_names(func):
    def wrapper(*args, **kwargs):
        id_dict = {device['id']: device['name'] for device in args[0].stick.config['devices']
                   if device['name'] in args[1]}
        func(args[0], id_dict)

    return wrapper


class DuofernCLI(Cmd):
    def __init__(self, serial_port=None, system_code=None, config_file=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stick = DuofernStickThreaded(serial_port=args.device, system_code=args.code,
                                          config_file_json=args.configfile)
        self.stick._initialize()
        self.stick.start()
        self.prompt = "duofern> "

    def emptyline(self):
        pass

    def do_pair(self, args):
        """
        Usage:
          pair <TIMEOUT>
        
        Start pairing mode. Pass a timeout in seconds as <TIMEOUT>.
        Will return after the timeout if no devices start pairing within the given timeout.
        
        Example:
        duofern> pair 10
            
        """
        timeout = 10
        if len(args) != 0:
            try:
                timeout = int(args[0])
            except:
                print("Please use an integer number to indicate TIMEOUT in seconds")
        print("Starting pairing mode... waiting  {} seconds".format(int(timeout)))
        self.stick.pair(timeout=timeout)
        time.sleep(args.pairtime + 0.5)
        self.stick.sync_devices()
        print("Pairing done, Config file updated.")

    def do_unpair(self, args):
        """
        Usage:
          unpair <TIMEOUT>

        Start pairing mode. Pass a timeout in seconds as <TIMEOUT>.
        Will return after the timeout if no devices start pairing within the given timeout.

        Example:
        duofern> unpair 10

        """
        timeout = 10
        if len(args) != 0:
            try:
                timeout = int(args[0])
            except:
                print("Please use an integer number to indicate TIMEOUT in seconds")
        print("Starting pairing mode... waiting  {} seconds".format(int(timeout)))
        self.stick.unpair(timeout=timeout)
        time.sleep(args.pairtime + 0.5)
        self.stick.sync_devices()
        print("Pairing done, Config file updated.")

    def do_remote(self, args):
        code = args[0][0:6]
        timeout = int(args[1])
        self.stick.remote(code, timeout)
        time.sleep(args.pairtime + 0.5)
        self.stick.sync_devices()
        print("Pairing done, Config file updated.")

    @splitargs
    @ids_for_names
    def do_up(self, blinds):
        """
        Usage:
          up <SHUTTER> [<SHUTTER> <SHUTTER>]
          
        Lift one or several shutters. Accepts a list of shutter names sepatated by space.
        
        Example:
            duofern> up Livingroom
            duofern> up Livingroom Kitchen
        """
        for blind_id in blinds:
            print("lifting {}".format(blinds[blind_id]))
            self.stick.command(blind_id, "up")

    @splitargs
    @ids_for_names
    def do_down(self, blinds):
        """
        Usage:
          up <SHUTTER> [<SHUTTER> <SHUTTER>...]

        Lower one or several shutters. Accepts a list of shutter names sepatated by space.

        Example:
            duofern> up Livingroom
            duofern> up Livingroom Kitchen
        """
        for blind_id in blinds:
            print("lowering {}".format(blinds[blind_id]))
            self.stick.command(blind_id, "down")

    @splitargs
    def do_rename(self, args):
        """
        Usage:
          rename <NAME> <NEW_NAME>
        
        Rename an actor. Write changes to config file when done.
        
        Example:
            duofern> rename 13f897 kitchen_west
        """
        id = [device['id'] for device in self.stick.config['devices'] if device['name'] == args[0]]
        if len(id)==0:
            print("Please enter a valid device name for renaming.")
        self.stick.set_name(id[0], args[1])
        print("Set name for {} to {}".format(id[0], args[0]))

    def refresh(self,args):
        """
        Usage:
          refresh
        
        Refresh config file with current changes. 
        
        example:
            duofern> refresh
        """
        self.stick.sync_devices()

    @splitargs
    @ids_for_names
    def do_on(self, blinds):
        """
        Usage:
          off <SWITCH1> [<SWITCH2> <SWITCH3>]

        Switch on one or several switch actors. Accepts a list of actor names.

        Example:
            duofern> off Livingroom
            duofern> off Livingroom Kitchen
        """
        for blind_id in blinds:
            print("lifting {}".format(blinds[blind_id]))
            self.stick.command(blind_id, "up")

    @splitargs
    @ids_for_names
    def do_off(self, blinds):
        """
        Usage:
          off <SWITCH1> [<SWITCH2> <SWITCH3>]

        Switch off one or several switch actors. Accepts a list of actor names.

        Example:
            duofern> off Livingroom
            duofern> off Livingroom Kitchen
        """
        for blind_id in blinds:
            print("lifting {}".format(blinds[blind_id]))
            self.stick.command(blind_id, "up")
