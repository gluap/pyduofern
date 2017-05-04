import argparse
import logging

from pyduofern.duofern_stick import DuofernStick

parser = argparse.ArgumentParser()
parser.add_argument('--device',
                    help='path to serial port created by duofern stick, defaults to first found serial port, typically'
                         'something like /dev/ttyUSB0 or /dev/rademacher if you use the provided udev rules file',
                    default=None)
parser.add_argument('--configfile', help='location of system config file', default=None)
parser.add_argument('--pair', action='store_true',
                    help='start pairing. Run this right before or after initializing pairing mode on your'
                         'device', default=False)
parser.add_argument('--code', help='set code for the system (warning, always use same code for once-paired devices)',
                    default=None)
parser.add_argument('--set_name', help='Set name for a device.', nargs=2, default=None,
                    metavar=("DEVICE_ID", "DEVICE_NAME"))
parser.add_argument('--list', help='list known devices', action='store_true', default=False)
parser.add_argument('--debug', help='enable verbose logging', action='store_true', default=False)

args = parser.parse_args()

if __name__ == "__main__":
    if args.debug:
        logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
    else:
        logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

    stick = DuofernStick(device=args.device, system_code=args.code, config_file_json=args.configfile)

    if args.set_name is not None:
        stick.set_name(args.set_name[0], args.set_name[1])

    elif args.pair:
        print("entering pairing mode")
        stick._initialize()
        stick.start()
    elif args.list:
        print("\n".join(
            ["id: {:6}    name: {}".format(device['id'], device['name']) for device in stick.config['devices']]))
