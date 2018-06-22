#!/usr/bin/env python3
# coding=utf-8
#   python interface for dufoern usb stick
#   Copyright (C) 2017 Paul Görgen
#   Rough python re-write of the FHEM duofern modules by telekatz, also licensed under GPLv2
#   This re-write contains only negligible amounts of original code
#   apart from some comments to facilitate translation of the not-yet
#   translated parts of the original software. Modification dates are
#   documented as submits to the git repository of this code, currently
#   maintained at https://github.com/gluap/pyduofern.git

#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.

#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.

#   You should have received a copy of the GNU General Public License
#   along with this program; if not, write to the Free Software Foundation,
#   Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301  USA

import asyncio
import logging
import time

from .definitions import *

# regexe for replacing:
# hash->\{([^\}]+)\}\{([^\}]+)\}
# hash['$1']['$2']
#
# ^([^\n]+=) \(([^?\n]+)\?([^:\n]+):([^\)\n]+)\)?#?
# $1 $3 if $2 else $4

logger = logging.getLogger(__file__)

duoStatusRequest = "0DFFnn400000000000000000000000000000yyyyyy01"
duoCommand = "0Dkknnnnnnnnnnnnnnnnnnnn000000zzzzzzyyyyyy00"
duoWeatherConfig = "0D001B400000000000000000000000000000yyyyyy00"
duoWeatherWriteConfig = "0DFF1Brrnnnnnnnnnnnnnnnnnnnn00000000yyyyyy00"
duoSetTime = "0D0110800001mmmmmmmmnnnnnn0000000000yyyyyy00"


def merge_dicts(*dict_args):
    """
    Given any number of dicts, shallow copy and merge into a new dict,
    precedence goes to key value pairs in latter dicts.
    """
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result


def DoTrigger(*args):
    logger.debug("called DoTrigger({})".format(args))


def readingsBulkUpdate(*args):
    pass


def readingsSingleUpdate(*args):
    pass


def readingsEndUpdate(*args):
    pass


def readingsBeginUpdate(*args):
    pass


def RemoveInternalTimer(*args):
    pass


def DUOFERN_DecodeWeatherSensorConfig(*args):
    pass


class Duofern(object):
    def __init__(self, send_hook=None, asyncio=False, changes_callback=None):
        self.asyncio = asyncio
        self.modules = {'by_code': {}}  # i guess this is supposed to be a hash of self.modules...
        self.ignore_devices = {}  # should replace attrValrel
        assert send_hook is not None, "Must define send callback"
        self.send_hook = send_hook
        self.changes_callback = changes_callback
        pass

    def add_device(self, code, name=None):
        if name is None:
            name = len(self.modules['by_code'])
        logger.debug("adding {}".format(code))
        self.modules['by_code'][code] = {'name': name}

    def del_device(self, code, name=None):
        if name is None:
            name = len(self.modules['by_code'])
        logger.info("removing {}".format(code))
        if code in self.modules['by_code']:
            del self.modules['by_code'][code]

    def update_state(self, code, key, value, trigger=None):
        self.modules['by_code'][code][key] = value
        if self.changes_callback:
            self.changes_callback()

    def delete_state(self, code, key):
        if key in self.modules['by_code'][code]:
            del self.modules['by_code'][code][key]

    def parse(self, msg):
        code = msg[30:36]
        if msg[0:2] == '81':
            code = msg[36:42]

        if code.lower() == 'ffffff':
            return
        # return hash->{NAME} if (code == "FFFFFF")

        try:
            module_definition = self.modules['by_code'][code]
        except KeyError:
            self.add_device(code)
            logger.info("detected unknown device, ID={}".format(code))
            module_definition = self.modules['by_code'][code]

        module_definition01 = None
        module_definition02 = None

        #        if not module_definition:
        #            DoTrigger("global", "Undefined code {}".format(code))
        #            # module_definition = self.modules['by_code']{code}
        #            logger.warning("Undefined code {}".format(code))
        #            raise DuofernException("Undefined code {}".format(code))

        hash = module_definition
        name = hash['name']

        if name in self.ignore_devices:
            return name

        # Device paired
        if msg[0:4] == "0602":
            self.update_state(code, "state", "paired", "1")
            # del hash['READINGS']['unpaired']
            logger.info("DUOFERN device paired, ID {}".format(code))

        # Device unpaired
        elif (msg[0:4] == "0603"):
            readingsBeginUpdate(hash)
            self.update_state(code, "unpaired", 1, "1")
            self.update_state(code, "state", "unpaired", "1")
            self.del_device(code)
            # readingsEndUpdate(hash, 1)  # Notify is done by Dispatch
            logger.warning("DUOFERN device unpaired, code {}".format(code))

        # Status Nachricht Aktor
        elif msg[0:6] == "0fff0f":
            format = msg[6:6 + 2]
            ver = msg[24:24 + 1] + msg[25:25 + 1]

            self.update_state(code, "version", ver, "0")

            # RemoveInternalTimer(hash)
            # del hash['helper']['timeout']

            # Bewegungsmelder, Wettersensor, Mehrfachwandtaster not tested yet
            if code[0:2] in ("65", "69", "74"):  # pragma: no cover
                self.update_state(code, "state", "OK", "1")
                module_definition01 = self.modules['by_code'][code + "01"]
                if not module_definition01:
                    DoTrigger("global", "UNDEFINED DUOFERN_code_actor DUOFERN code01")
                    module_definition01 = self.modules['by_code'][code + "01"]

            # Universalaktor -- not tested yet
            elif code[0:2] == "43":  # pragma: no cover
                self.update_state(code, "state", "OK", "1")
                module_definition01 = self.modules['by_code'][code + "01"]
                if not module_definition01:
                    DoTrigger("global", "UNDEFINED DUOFERN_code+_01 DUOFERN code+01")
                    module_definition01 = self.modules['by_code'][code + "01"]

                module_definition02 = self.modules['by_code'][code + "02"]
                if not module_definition02:
                    DoTrigger("global", "UNDEFINED DUOFERN_code+_02 DUOFERN code02")
                    module_definition02 = self.modules['by_code'][code + "02"]

            if module_definition01:
                hash = module_definition01

            # RolloTron
            if format == "21":
                pos = int(msg[22:22 + 2], 16) & 0x7F
                ventPos = int(msg[12:12 + 2], 16) & 0x7F
                ventMode = "on" if int(msg[12:12 + 2], 16) & 0x80 else "off"
                sunPos = int(msg[20:20 + 2], 16) & 0x7F
                sunMode = "on" if int(msg[20:20 + 2], 16) & 0x80 else "off"
                timerAuto = "on" if int(msg[8:8 + 2], 16) & 0x01 else "off"
                sunAuto = "on" if int(msg[8:8 + 2], 16) & 0x04 else "off"
                dawnAuto = "on" if int(msg[10:10 + 2], 16) & 0x08 else "off"
                duskAuto = "on" if int(msg[8:8 + 2], 16) & 0x08 else "off"
                manualMode = "on" if int(msg[8:8 + 2], 16) & 0x80 else "off"

                state = pos
                state = "opened" if (pos == 0) else pos
                state = "closed" if (pos == 100) else pos

                readingsBeginUpdate(hash)
                self.update_state(code, "ventilatingPosition", ventPos, "1")
                self.update_state(code, "ventilatingMode", ventMode, "1")
                self.update_state(code, "sunPosition", sunPos, "1")
                self.update_state(code, "sunMode", sunMode, "1")
                self.update_state(code, "timeAutomatic", timerAuto, "1")
                self.update_state(code, "sunAutomatic", sunAuto, "1")
                self.update_state(code, "dawnAutomatic", dawnAuto, "1")
                self.update_state(code, "duskAutomatic", duskAuto, "1")
                self.update_state(code, "manualMode", manualMode, "1")
                self.update_state(code, "position", pos, "1")
                self.update_state(code, "state", state, "1")
                self.update_state(code, "moving", "stop", "1")
                readingsEndUpdate(hash, 1)  # Notify is done by Dispatch

            # Universal Aktor, Steckdosenaktor, Troll Comfort DuoFern (Lichtmodus) not tested yet
            elif format == "22":  # pragma: no cover
                level = int(msg[22:22 + 2], 16) & 0x7F
                modeChange = "on" if int(msg[22:22 + 2], 16) & 0x80 else "off"
                sunMode = "on" if int(msg[14:14 + 2], 16) & 0x10 else "off"
                timerAuto = "on" if int(msg[14:14 + 2], 16) & 0x01 else "off"
                sunAuto = "on" if int(msg[14:14 + 2], 16) & 0x04 else "off"
                dawnAuto = "on" if int(msg[14:14 + 2], 16) & 0x40 else "off"
                duskAuto = "on" if int(msg[14:14 + 2], 16) & 0x02 else "off"
                manualMode = "on" if int(msg[14:14 + 2], 16) & 0x20 else "off"
                stairwellFunction = "on" if int(msg[16:16 + 4], 16) & 0x8000 else "off"
                stairwellTime = (int(msg[16:16 + 4], 16) & 0x7FFF) / 10

                state = level
                state = "off" if (level == 0) else level
                state = "on" if (level == 100) else level

                readingsBeginUpdate(hash)
                self.update_state(code, "sunMode", sunMode, "1")
                self.update_state(code, "timeAutomatic", timerAuto, "1")
                self.update_state(code, "sunAutomatic", sunAuto, "1")
                self.update_state(code, "dawnAutomatic", dawnAuto, "1")
                self.update_state(code, "duskAutomatic", duskAuto, "1")
                self.update_state(code, "manualMode", manualMode, "1")
                self.update_state(code, "modeChange", modeChange, "1")
                self.update_state(code, "stairwellFunction", stairwellFunction, "1")
                self.update_state(code, "stairwellTime", stairwellTime, "1")
                self.update_state(code, "level", level, "1")
                self.update_state(code, "state", state, "1")
                readingsEndUpdate(hash, 1)

                if module_definition02:
                    hash = module_definition02
                    level = int(msg[20:20 + 2], 16) & 0x7F
                    modeChange = "on" if int(msg[20:20 + 2], 16) & 0x80 else "off"
                    sunMode = "on" if int(msg[12:12 + 2], 16) & 0x10 else "off"
                    timerAuto = "on" if int(msg[12:12 + 2], 16) & 0x01 else "off"
                    sunAuto = "on" if int(msg[12:12 + 2], 16) & 0x04 else "off"
                    dawnAuto = "on" if int(msg[12:12 + 2], 16) & 0x40 else "off"
                    duskAuto = "on" if int(msg[12:12 + 2], 16) & 0x02 else "off"
                    manualMode = "on" if int(msg[12:12 + 2], 16) & 0x20 else "off"
                    stairwellFunction = "on" if int(msg[8:8 + 4], 16) & 0x8000 else "off"
                    stairwellTime = (int(msg[8:8 + 4], 16) & 0x7FFF) / 10

                    state = level
                    state = "off" if (level == 0) else level
                    state = "on" if (level == 100) else level

                    readingsBeginUpdate(hash)
                    self.update_state(code, "sunMode", sunMode, "1")
                    self.update_state(code, "timeAutomatic", timerAuto, "1")
                    self.update_state(code, "sunAutomatic", sunAuto, "1")
                    self.update_state(code, "dawnAutomatic", dawnAuto, "1")
                    self.update_state(code, "duskAutomatic", duskAuto, "1")
                    self.update_state(code, "manualMode", manualMode, "1")
                    self.update_state(code, "modeChange", modeChange, "1")
                    self.update_state(code, "stairwellFunction", stairwellFunction, "1")
                    self.update_state(code, "stairwellTime", stairwellTime, "1")
                    self.update_state(code, "level", level, "1")
                    self.update_state(code, "state", state, "1")
                    readingsEndUpdate(hash, 1)  # Notify is done by Dispatch
            elif format == "23":
                pos = int(msg[22:22 + 2], 16) & 0x7F
                reversal = "on" if int(msg[22:22 + 2], 16) & 0x80 else "off"
                ventPos = int(msg[16:16 + 2], 16) & 0x7F
                ventMode = "on" if int(msg[16:16 + 2], 16) & 0x80 else "off"
                sunPos = int(msg[18:18 + 2], 16) & 0x7F
                sunMode = "on" if int(msg[14:14 + 2], 16) & 0x10 else "off"
                timerAuto = "on" if int(msg[14:14 + 2], 16) & 0x01 else "off"
                sunAuto = "on" if int(msg[14:14 + 2], 16) & 0x04 else "off"
                dawnAuto = "on" if int(msg[12:12 + 2], 16) & 0x02 else "off"
                duskAuto = "on" if int(msg[14:14 + 2], 16) & 0x02 else "off"
                manualMode = "on" if int(msg[14:14 + 2], 16) & 0x20 else "off"
                windAuto = "on" if int(msg[14:14 + 2], 16) & 0x40 else "off"
                windMode = "on" if int(msg[14:14 + 2], 16) & 0x08 else "off"
                windDir = "down" if int(msg[12:12 + 2], 16) & 0x04 else "up"
                rainAuto = "on" if int(msg[14:14 + 2], 16) & 0x80 else "off"
                rainMode = "on" if int(msg[12:12 + 2], 16) & 0x01 else "off"
                rainDir = "down" if int(msg[12:12 + 2], 16) & 0x08 else "up"
                runningTime = int(msg[20:20 + 2], 16)
                deadTime = int(msg[12:12 + 2], 16) & 0x30
                blindsMode = "on" if int(msg[26:26 + 2], 16) & 0x80 else "off"
                tiltInSunPos = "on" if int(msg[18:18 + 2], 16) & 0x80 else "off"
                tiltInVentPos = "on" if int(msg[8:8 + 2], 16) & 0x80 else "off"
                tiltAfterMoveLevel = "on" if int(msg[8:8 + 2], 16) & 0x40 else "off"
                tiltAfterStopDown = "on" if int(msg[10:10 + 2], 16) & 0x80 else "off"
                module_definitionaultSlatPos = int(msg[10:10 + 2], 16) & 0x7F
                slatRunTime = int(msg[8:8 + 2], 16) & 0x3F
                slatPosition = int(msg[26:26 + 2], 16) & 0x7F

                state = "opened" if (pos == 0) else pos
                state = "closed" if (pos == 100) else state

                readingsBeginUpdate(hash)
                self.update_state(code, "ventilatingPosition", ventPos, "1")
                self.update_state(code, "ventilatingMode", ventMode, "1")
                self.update_state(code, "sunPosition", sunPos, "1")
                self.update_state(code, "sunMode", sunMode, "1")
                self.update_state(code, "timeAutomatic", timerAuto, "1")
                self.update_state(code, "sunAutomatic", sunAuto, "1")
                self.update_state(code, "dawnAutomatic", dawnAuto, "1")
                self.update_state(code, "duskAutomatic", duskAuto, "1")
                self.update_state(code, "manualMode", manualMode, "1")
                self.update_state(code, "windAutomatic", windAuto, "1")
                self.update_state(code, "windMode", windMode, "1")
                self.update_state(code, "windDirection", windDir, "1")
                self.update_state(code, "rainAutomatic", rainAuto, "1")
                self.update_state(code, "rainMode", rainMode, "1")
                self.update_state(code, "rainDirection", rainDir, "1")
                self.update_state(code, "runningTime", runningTime, "1")
                self.update_state(code, "motorDeadTime", deadTimes[deadTime], "1")
                self.update_state(code, "position", pos, "1")
                self.update_state(code, "reversal", reversal, "1")
                self.update_state(code, "blindsMode", blindsMode, "1")

                # not tested yet
                if blindsMode == "on":  # pragma: no cover
                    self.update_state(code, "tiltInSunPos", tiltInSunPos, "1")
                    self.update_state(code, "tiltInVentPos", tiltInVentPos, "1")
                    self.update_state(code, "tiltAfterMoveLevel", tiltAfterMoveLevel, "1")
                    self.update_state(code, "tiltAfterStopDown", tiltAfterStopDown, "1")
                    self.update_state(code, "module_definitionaultSlatPos", module_definitionaultSlatPos, "1")
                    self.update_state(code, "slatRunTime", slatRunTime, "1")
                    self.update_state(code, "slatPosition", slatPosition, "1")
                else:
                    self.delete_state(code, 'tiltInSunPos')
                    self.delete_state(code, 'tiltInVentPos')
                    self.delete_state(code, 'tiltAfterMoveLevel')
                    self.delete_state(code, 'tiltAfterStopDown')
                    self.delete_state(code, 'module_definitionaultSlatPos')
                    self.delete_state(code, 'slatRunTime')
                    self.delete_state(code, 'slatPosition')

                self.update_state(code, "moving", "stop", "1")
                self.update_state(code, "state", state, "1")
                readingsEndUpdate(hash, 1)  # Notify is done by Dispatch
            # Rohrmotor, SX5  -- not tested yet
            elif format == "24":  # pragma: no cover

                pos = int(msg[22:22 + 2], 16) & 0x7F
                reversal = "on" if int(msg[22:22 + 2], 16) & 0x80 else "off"
                ventPos = int(msg[16:16 + 2], 16) & 0x7F
                ventMode = "on" if int(msg[16:16 + 2], 16) & 0x80 else "off"
                sunPos = int(msg[18:18 + 2], 16) & 0x7F
                sunMode = "on" if int(msg[14:14 + 2], 16) & 0x10 else "off"
                timerAuto = "on" if int(msg[14:14 + 2], 16) & 0x01 else "off"
                sunAuto = "on" if int(msg[14:14 + 2], 16) & 0x04 else "off"
                dawnAuto = "on" if int(msg[12:12 + 2], 16) & 0x02 else "off"
                duskAuto = "on" if int(msg[14:14 + 2], 16) & 0x02 else "off"
                manualMode = "on" if int(msg[14:14 + 2], 16) & 0x20 else "off"
                windAuto = "on" if int(msg[14:14 + 2], 16) & 0x40 else "off"
                windMode = "on" if int(msg[14:14 + 2], 16) & 0x08 else "off"
                windDir = "down" if int(msg[12:12 + 2], 16) & 0x04 else "up"
                rainAuto = "on" if int(msg[14:14 + 2], 16) & 0x80 else "off"
                rainMode = "on" if int(msg[12:12 + 2], 16) & 0x01 else "off"
                rainDir = "down" if int(msg[12:12 + 2], 16) & 0x08 else "up"
                obstacle = "1" if int(msg[12:12 + 2], 16) & 0x10 else "0"
                block = "1" if int(msg[12:12 + 2], 16) & 0x40 else "0"
                lightCurtain = "1" if int(msg[8:8 + 2], 16) & 0x80 else "0"
                autoClose = int(msg[10:10 + 2], 16) & 0x0F
                openSpeed = int(msg[10:10 + 2], 16) & 0x30
                alert2000 = "on" if int(msg[10:10 + 2], 16) & 0x80 else "off"
                backJump = "on" if int(msg[26:26 + 2], 16) & 0x01 else "off"
                alert10 = "on" if int(msg[26:26 + 2], 16) & 0x02 else "off"

                state = pos
                state = "opened" if (pos == 0) else pos
                state = "closed" if (pos == 100) else pos
                state = "light curtain" if (lightCurtain == "1") else pos
                state = "obstacle" if (obstacle == "1") else pos
                state = "block" if (block == "1") else pos

                readingsBeginUpdate(hash)
                self.update_state(code, "manualMode", manualMode, "1")
                self.update_state(code, "timeAutomatic", timerAuto, "1")
                self.update_state(code, "ventilatingPosition", ventPos, "1")
                self.update_state(code, "ventilatingMode", ventMode, "1")
                self.update_state(code, "position", pos, "1")
                self.update_state(code, "state", state, "1")
                self.update_state(code, "obstacle", obstacle, "1")
                self.update_state(code, "block", block, "1")
                self.update_state(code, "moving", "stop", "1")

                if code[0:2] == "4E":  # SX5
                    self.update_state(code, "10minuteAlarm", alert10, "1")
                    self.update_state(code, "automaticClosing", closingTimes['autoClose'], "1")
                    self.update_state(code, "2000cycleAlarm", alert2000, "1")
                    self.update_state(code, "openSpeed", openSpeeds['openSpeed'], "1")
                    self.update_state(code, "backJump", backJump, "1")
                    self.update_state(code, "lightCurtain", lightCurtain, "1")
                else:
                    self.update_state(code, "sunPosition", sunPos, "1")
                    self.update_state(code, "sunMode", sunMode, "1")
                    self.update_state(code, "sunAutomatic", sunAuto, "1")
                    self.update_state(code, "dawnAutomatic", dawnAuto, "1")
                    self.update_state(code, "duskAutomatic", duskAuto, "1")
                    self.update_state(code, "windAutomatic", windAuto, "1")
                    self.update_state(code, "windMode", windMode, "1")
                    self.update_state(code, "windDirection", windDir, "1")
                    self.update_state(code, "rainAutomatic", rainAuto, "1")
                    self.update_state(code, "rainMode", rainMode, "1")
                    self.update_state(code, "rainDirection", rainDir, "1")
                    self.update_state(code, "reversal", reversal, "1")

                readingsEndUpdate(hash, 1)

                # Dimmaktor -- not tested yet
            elif format == "25":  # pragma: no cover
                stairwellFunction = "on" if int(msg[10:10 + 4], 16) & 0x8000 else "off"
                stairwellTime = (int(msg[10:10 + 4], 16) & 0x7FFF) / 10
                timerAuto = "on" if int(msg[14:14 + 2], 16) & 0x01 else "off"
                duskAuto = "on" if int(msg[14:14 + 2], 16) & 0x02 else "off"
                sunAuto = "on" if int(msg[14:14 + 2], 16) & 0x04 else "off"
                sunMode = "on" if int(msg[14:14 + 2], 16) & 0x08 else "off"
                manualMode = "on" if int(msg[14:14 + 2], 16) & 0x20 else "off"
                dawnAuto = "on" if int(msg[14:14 + 2], 16) & 0x40 else "off"
                intemedSave = "on" if int(msg[14:14 + 2], 16) & 0x80 else "off"
                runningTime = int(msg[18:18 + 2], 16)
                intemedVal = int(msg[20:20 + 2], 16) & 0x7F
                intermedMode = "on" if int(msg[20:20 + 2], 16) & 0x80 else "off"
                level = int(msg[22:22 + 2], 16) & 0x7F
                modeChange = "on" if int(msg[22:22 + 2], 16) & 0x80 else "off"

                state = level
                state = "off" if (level == 0) else level
                state = "on" if (level == 100) else level

                readingsBeginUpdate(hash)
                self.update_state(code, "stairwellFunction", stairwellFunction, "1")
                self.update_state(code, "stairwellTime", stairwellTime, "1")
                self.update_state(code, "timeAutomatic", timerAuto, "1")
                self.update_state(code, "duskAutomatic", duskAuto, "1")
                self.update_state(code, "sunAutomatic", sunAuto, "1")
                self.update_state(code, "sunMode", sunMode, "1")
                self.update_state(code, "manualMode", manualMode, "1")
                self.update_state(code, "dawnAutomatic", dawnAuto, "1")
                self.update_state(code, "saveIntermediateOnStop", intemedSave, "1")
                self.update_state(code, "runningTime", runningTime, "1")
                self.update_state(code, "intermediateValue", intemedVal, "1")
                self.update_state(code, "intermediateMode", intermedMode, "1")
                self.update_state(code, "level", level, "1")
                self.update_state(code, "modeChange", modeChange, "1")
                self.update_state(code, "state", state, "1")
                readingsEndUpdate(hash, 1)  # Notify is done by Dispatch

            # Thermostat -- not tested yet
            elif format == "27":  # pragma: no cover
                temperature1 = "%0.1f" % (((int(msg[8:8 + 4], 16) & 0x07FF) - 400) / 10)
                temperature2 = "%0.1f" % (((int(msg[12:12 + 4], 16) & 0x07FF) - 400) / 10)
                tempThreshold1 = "%0.1f" % ((int(msg[16:16 + 2], 16) - 80) / 2)
                tempThreshold2 = "%0.1f" % ((int(msg[18:18 + 2], 16) - 80) / 2)
                tempThreshold3 = "%0.1f" % ((int(msg[20:20 + 2], 16) - 80) / 2)
                tempThreshold4 = "%0.1f" % ((int(msg[22:22 + 2], 16) - 80) / 2)
                desiredTemp = "%0.1f" % ((int(msg[26:26 + 2], 16) - 80) / 2)
                output = "on" if int(msg[8:8 + 2], 16) & 0x08 else "off"
                manualOverride = "on" if int(msg[8:8 + 2], 16) & 0x10 else "off"
                actTempLimit = (int(msg[8:8 + 2], 16) & 0x60) >> 5
                timerAuto = "on" if int(msg[12:12 + 2], 16) & 0x08 else "off"
                manualMode = "on" if int(msg[12:12 + 2], 16) & 0x10 else "off"

                state = "T: temperature1 desired: desiredTemp"

                readingsBeginUpdate(hash)
                self.update_state(code, "measured-temp", temperature1, "1")
                self.update_state(code, "measured-temp2", temperature2, "1")
                self.update_state(code, "temperatureThreshold1", tempThreshold1, "1")
                self.update_state(code, "temperatureThreshold2", tempThreshold2, "1")
                self.update_state(code, "temperatureThreshold3", tempThreshold3, "1")
                self.update_state(code, "temperatureThreshold4", tempThreshold4, "1")
                self.update_state(code, "desired-temp", desiredTemp, "1")
                self.update_state(code, "output", output, "1")
                self.update_state(code, "manualOverride", manualOverride, "1")
                self.update_state(code, "actTempLimit", actTempLimit, "1")
                self.update_state(code, "timeAutomatic", timerAuto, "1")
                self.update_state(code, "manualMode", manualMode, "1")

                self.update_state(code, "state", state, "1")
                readingsEndUpdate(hash, 1)

            else:
                logger.warning("DUOFERN unknown msg: {}".format(msg))


        # Wandtaster, Funksender UP, Handsender, Sensoren
        elif msg[0:2] == "0f" and msg[4:6] in ['07', '0e']:  # pragma: no cover
            id = msg[4:4 + 4]

            if id not in sensorMsg:
                logger.warning("unknown message {}".format(msg))

            chan = msg[sensorMsg['id']['chan'] * 2 + 2:sensorMsg['id']['chan'] * 2 + 4]
            if code[0:2] in ("61", "70", "71"):
                chan = "01"

            chans = []
            if (sensorMsg['id'][chan] == 5):
                chanCount = 4 if (code[0:2] == "73") else 5
                for x in range(0, chanCount):
                    if ((0x01 << x) & int(chan, 16)):
                        chans.append(x + 1)


            else:
                chans.append(chan)

            if code[0:2] in ("65", "69", "74"):
                module_definition01 = self.modules['by_code'][code + "00"]
            if not module_definition01:
                DoTrigger("global", "UNDEFINED DUOFERN_code_sensor DUOFERN code00")
                module_definition01 = self.modules['by_code'][code + "00"]

            if (module_definition01):
                hash = module_definition01

            for chan in chans:
                if id[2:4] in ("1a", "18", "19", "01", "02", "03"):
                    if (id[2:4] == "1a") or (id[0:2] == "0e") or (code[0:2] in ("a0", "a2")):
                        self.update_state(code, "state", sensorMsg['id']['state'] + "." + chan, "1")
                    else:
                        self.update_state(code, "state", sensorMsg['id']['state'], "1")

                    self.update_state(code, "channelchan", sensorMsg['id']['name'], "1")
                else:
                    if (code[0:2] not in ("69", "73")) or (id[2:4] in ("11", "12")):
                        chan = ""
                    if code[0:2] in ("65", "a5", "aa", "ab"):
                        self.update_state(code, "state", sensorMsg['id']['state'], "1")

                    self.update_state(code, "event", sensorMsg['id']['name'] + "." + chan, "1")
                    DoTrigger(hash["name"], sensorMsg['id'][name] + "." + chan)



        # Umweltsensor Wetter -- not tested yet
        elif msg[0:8] == "0f011322":  # pragma: no cover
            module_definition01 = self.modules['by_code'][code + "00"]
            if not module_definition01:
                DoTrigger("global", "UNDEFINED DUOFERN_code_sensor DUOFERN code00")
                module_definition01 = self.modules['by_code'][code + "00"]

            hash = module_definition01

            brightnessExp = 1000 if int(msg[8:8 + 4], 16) & 0x0400 else 1
            brightness = (int(msg[8:8 + 4], 16) & 0x01FF) * brightnessExp
            sunDirection = int(msg[14:14 + 2], 16) * 1.5
            sunHeight = int(msg[16:16 + 2], 16) - 90
            temperature = ((int(msg[18:18 + 4], 16) & 0x7FFF) - 400) / 10
            isRaining = 1 if int(msg[18:18 + 4], 16) & 0x8000 else 0
            wind = (int(msg[22:22 + 4], 16) & 0x03FF) / 10

            state = "T: {}".format(temperature)
            state += " W: {}".format(wind)
            state += " IR: ".format(isRaining)
            state += " B: ".format(brightness)

            readingsBeginUpdate(hash)
            self.update_state(code, "brightness", brightness, "1")
            self.update_state(code, "sunDirection", sunDirection, "1")
            self.update_state(code, "sunHeight", sunHeight, "1")
            self.update_state(code, "temperature", temperature, "1")
            self.update_state(code, "isRaining", isRaining, "1")
            self.update_state(code, "state", state, "1")
            self.update_state(code, "wind", wind, "1")
            readingsEndUpdate(hash, 1)  # Notify is done by Dispatch

        # Umweltsensor Zeit
        elif msg[0:8] == "0fff1020":  # pragma: no cover
            module_definition01 = self.modules['by_code'][code + "00"]
            if (not module_definition01):
                DoTrigger("global", "UNDEFINED DUOFERN_code_sensor DUOFERN code00")
                module_definition01 = self.modules['by_code'][code + "00"]

            hash = module_definition01

            year = msg[12:12 + 2]
            month = msg[14:14 + 2]
            day = msg[18:18 + 2]
            hour = msg[20:20 + 2]
            minute = msg[22:22 + 2]
            second = msg[24:24 + 2]

            readingsBeginUpdate(hash)
            self.update_state(code, "date", "20" + str(year) + "-" + str(month) + "-" + str(day), "1")
            self.update_state(code, "time", str(hour) + ":" + str(minute) + ":" + str(second), "1")
            readingsEndUpdate(hash, 1)  # Notify is done by Dispatch

        # Umweltsensor Konfiguration
        elif msg[0:7] == "0fff1b2" and msg[7] in ["0", "1", "2", "3", "4", "5", "6", "7", "8"]:  # pragma: no cover
            reg = msg[6:6 + 2] - 21
            regVal = msg[8:8 + 20]

            module_definition01 = self.modules['by_code'][code + "00"]
            if not module_definition01:
                DoTrigger("global", "UNDEFINED DUOFERN_code_sensor DUOFERN {}00".format(code))
                module_definition01 = self.modules['by_code'][code + "00"]

            hash = module_definition01

            del hash['READINGS']['configModified']
            self.update_state(code, ".regreg", "regVal", "1")
            # self.update_state(code, "regreg", "regVal", "1")
            DUOFERN_DecodeWeatherSensorConfig(hash)

            # Rauchmelder Batterie
        elif msg[0:8] == "0fff1323":  # pragma: no cover
            battery = "low" if int(msg[8:8 + 2], 16) <= 10 else "ok"
            batteryLevel = int(msg[8:8 + 2], 16)

            readingsBeginUpdate(hash)
            self.update_state(code, "battery", battery, "1")
            self.update_state(code, "batteryLevel", batteryLevel, "1")
            readingsEndUpdate(hash, 1)  # Notify is done by Dispatch

            # ACK, Befehl vom Aktor empfangen
        elif msg[0:8] == "810003cc":
            hash['helper']['timeout']['t'] = hash['name']["timeout"]["60"]
            ##InternalTimer(gettimeofday()+hash['helper']['timeout']{t}, "DUOFERN_StatusTimeout", hash, 0)
            hash['helper']['timeout']['count'] = 4

        # NACK, Befehl nicht vom Aktor empfangen
        elif msg[0:8] == "810108aa":
            logger.warning("missing ack for {}".format(hash))
            # self.update_state(code, "state", "MISSING ACK", "1")
            # foreach (grep (/^channel_/, keys%{hash})){
            #   chnHash = module_definitions{hash->{_}}
            #   readingsSingleUpdate(chnHash, "state", "MISSING ACK", 1)
            # }
            # Log3 hash, 3, "DUOFERN error: name MISSING ACK"

        else:
            logger.warning("Unknown msg: {}".format(msg))

        if module_definition01:
            DoTrigger(module_definition01['name'], None)
        if module_definition02:
            DoTrigger(module_definition02['name'], None)

        return name

    @asyncio.coroutine
    def send(self, cmd):
        yield from self.send_hook(cmd)

    @asyncio.coroutine
    def set(self, code, cmd, *args):
        # my (hash, @a) = @_
        # b = @a

        # return "set name needs at least one parameter" if(@a < 2)

        #        me     = shift @a
        #        cmd    = shift @a
        arg = args[0] if len(args) >= 1 else None
        arg2 = args[1] if len(args) > 1 else None
        code = code[0:0 + 6]
        name = self.modules['by_code'][code]['name']

        # sets

        if code[0:2] == "49":
            sets = merge_dicts(setsBasic, setsDefaultRollerShutter, setsRolloTube)
        if code[0:2] in ("42", "4b", "4c", "70"):
            sets = merge_dicts(setsBasic, setsDefaultRollerShutter, setsTroll, {"blindsMode:on,off": ""})
        if code[0:2] == "47":
            sets = merge_dicts(setsBasic, setsDefaultRollerShutter, setsTroll)
        if code[0:2] in ("40", "41", "61"):
            sets = merge_dicts(setsBasic, setsDefaultRollerShutter)  # if (code =~ /^(40|41|61)..../)
        if code[0:2] == "69":
            sets = merge_dicts(setsBasic, setsUmweltsensor)  # if (code =~ /^69..../)
        if code[0:2] == "69" and len(code) >= 8 and code[6:8] == "00":
            sets = merge_dicts(setsUmweltsensor00)  # if (code =~ /^69....00/)
        if code[0:2] == "69" and len(code) >= 8 and code[6:8] == "01":
            sets = merge_dicts(setsDefaultRollerShutter, setsUmweltsensor01)  # if (code =~ /^69....01/)
        if code[0:2] == "43" and len(code) >= 8 and code[6:8] in ("01", "02"):
            sets = merge_dicts(*setsSwitchActor)  # if (code =~ /^43....(01|02)/)
        if code[0:2] in ("43", "65", "74"):
            sets = merge_dicts(setsBasic, {"getStatus:noArg": ""})  # if (code =~ /^(43|65|74)..../)
        if code[0:2] in ("46", "71"):
            sets = merge_dicts(setsBasic, setsSwitchActor)  # if (code =~ /^(46|71)..../)
        if code[0:2] == "4e":
            sets = merge_dicts(setsBasic, setsSX5)  # if (code =~ /^4E..../)
        if code[0:2] == "48":
            sets = merge_dicts(setsBasic, setsDimmer)  # if (code =~ /^48..../)
        if code[0:2] == "73":
            sets = merge_dicts(setsBasic, setsThermostat)  # if (code =~ /^73..../)
        if code[0:2] in ("65", "74") and len(code) >= 8 and code[6:8] == "01":
            sets = merge_dicts(setsSwitchActor)  # if (code =~ /^(65|74)....01/)

        blindsMode = "off" if not "blindsMode" in self.modules['by_code'][code] else self.modules['by_code'][code]
        if (blindsMode == "on"):
            sets = merge_dicts(sets, setsBlinds)

        logger.debug(sets.keys())  # join(" ", sort keys sets)
        if cmd in commandsStatus:
            buf = duoStatusRequest
            buf = buf.replace("nn", commandsStatus[cmd])
            buf = buf.replace("yyyyyy", code)
            yield from self.send(buf)
            return None

        elif cmd == "clear":
            keys = self.modules['by_code'][code].keys()
            for key in keys:
                if key != 'name':
                    self.modules['by_code'][code].__delitem__(key)
            return None
            # cH = (hash)
            # delete _->{READINGS} foreach (@cH)
            # return undef

        elif cmd == "getConfig":
            buf = duoWeatherConfig
            buf = buf.replace("yyyyyy", code)
            yield from self.send(buf)
            return None

        elif cmd == "writeConfig":
            for x in range(0, 8):
                # for(my x=0; x<8; x++)    {
                regV = "00000000000000000000" if not ".reg{}".format(x) in self.modules['by_code'][code] else \
                    self.modules['by_code'][code][".reg{}".format(x)]
                reg = "%02x" % (x + 0x81)
                buf = duoWeatherWriteConfig
                buf = buf.replace("yyyyyy", code)
                buf = buf.replace("rr", reg)
                buf = buf.replace("nnnnnnnnnnnnnnnnnnnn", regV)
                yield from self.send(buf)
                self.send(buf)

            if "configModified" in self.modules['by_code'][code]:
                self.modules['by_code'][code].__delitem__("configModified")

            # delete hash->{READINGS}{configModified}
            return None

        elif cmd == "time":
            buf = duoSetTime

            # my (sec,min,hour,mday,month,year,wday,yday,isdst) = localtime

            year, month, mday, hour, min, sec, wday, yday, isdst, = time.localtime()

            wday = wday - 1 if wday != 0 else 7  # wday = (wday==0 ? 7 : wday-1)
            m = "%02d%02d%02d%02d" % (year - 100, month + 1, wday, mday)
            n = "%02d%02d%02d" % (hour, min, sec)

            buf = buf.replace("mmmmmmmm", m)
            buf = buf.replace("nnnnnn", n)
            buf = buf.replace("yyyyyy", code)
            yield from self.send(buf)
            return None

        elif cmd in wCmds:
            logger.error("this has not been implemented yet")
            # if code[0:2] =="69" and len(code)>=8 and code[6:8] == "00":
            #     return "This command is not allowed for this device."
            # regs=[]
            # if len(args)<1:
            #     return "Missing argument"
            #
            # local_args = args + ("off","off","off","off")
            #
            # for x in range(0,8):#for(my x=0; x<8; x++)    {
            #     temp="00000000000000000000" if not ".regx" in self.modules['by_code'][code] else self.modules['by_code'][code][".regx"]
            #     regs.append(temp)
            #
            #
            # if cmd ==  "triggerSun":
            #     logger.error("this needs to be implemented (triggerSun)")
            #     # newargs=[]
            #     # for _arg in args:
            #     #     if (_arg != "off"):
            #     #         args2 = _arg.split(":")
            #     #         temp = _arg
            #     #         #return "Wrong argument _" if (args2[0] !~ m/^\d+/ || args2[0] < 1 || args2[0] > 100)
            #     #         #return "Wrong argument _" if (args2[1] !~ m/^\d+/ || args2[1] < 1 || args2[1] > 30)
            #     #         #return "Wrong argument _" if (args2[2] !~ m/^\d+/ || args2[2] < 1 || args2[2] > 30)
            #     #
            #     #         if (len(args2) < 3):
            #     #             return "Missing argument"
            #     #         if (int(args2[0]) < 1 or args2[0] > 100) or\
            #     #              (int(args2[1]) < 1 or args2[1] > 30) or\
            #     #              (int(args2[2]) < 1 or args2[2] > 30):
            #     #             return "Wrong argument {}".format(_arg)
            #     #         _arg = ((args2[0]-1)<<12) | ((args2[1]-1)<<19) | ((args2[2]-1)<<24)
            #     #
            #     #         if(len(args2) > 3):
            #     #             if (int(args2[3]) < -5 or int(args2[3]) > 26):
            #     #                 return "Wrong argument {}".format(temp)
            #     #             _arg |= (((int(args2[3]) + 5) << 7) | 0x40)
            #     #     newargs.append(arg)
            #     # args=newargs
            #
            #
            #
            #
            #
            # if cmd ==  "triggerSunDirection":
            #     logger.error("not implemented (triggersundirection)")
            #     # for(my x=0; x<5; x++)    {
            #     #     if (args[x] ne "off") {
            #     #         args2 = split(/:/, args[x])
            #     #         return "Missing argument" if(@args2 < 2)
            #     #         return "Wrong argument args[x]" if (args2[0] !~ m/^\d+(\.\d+|)/ || args2[0] < 0 || args2[0] > 315)
            #     #         return "Wrong argument args[x]" if (args2[1] !~ m/^\d+/ || args2[1] < 45 || args2[1] > 180)
            #     #         args2[0] = int((args2[0]+11.25)/22.5)
            #     #         args2[1] = int((args2[1]+22.5)/45)
            #     #         args2[0] = 15 - (args2[1]*2) if ((args2[0] + args2[1]*2) > 15)
            #     #         args[x] = (args2[0]+args2[1]) | ((args2[1])<<4) | 0x80
            #     #     } else {
            #     #         tSunHeight = map{hex(_)} unpack 'x66A2x8A2x8A2x8A2x8A2', regs
            #     #         if (tSunHeight[x] & 0x18) {
            #     #             args[x] = 0x81
            #     #         } else {
            #     #             args[x] = 0x01
            #     #         }
            #     #     }
            #     # }
            # }
            #
            # if cmd ==  "triggerSunHeight":
            #     logger.error("not implemented (triggersundirection)")
            #     #
            #     #
            #     # for(my x=0; x<5; x++)    {
            #     #     if (args[x] ne "off") {
            #     #         args2 = split(/:/, args[x])
            #     #         return "Missing argument" if(@args2 < 2)
            #     #         return "Wrong argument1 args[x]" if (args2[0] !~ m/^\d+/ || args2[0] < 0 || args2[0] > 90)
            #     #         return "Wrong argument2 args[x]" if (args2[1] !~ m/^\d+/ || args2[1] < 20 || args2[1] > 60)
            #     #         args2[0] = int((args2[0]+6.5)/13)
            #     #         args2[1] = int((args2[1]+13)/26)
            #     #         args2[0] = 7 - (args2[1]*2) if ((args2[0] + args2[1]*2) > 7)
            #     #         args[x] = ((args2[0]+args2[1])<<8) | ((args2[1])<<11) | 0x80
            #     #     } else {
            #     #         tSunDir = map{hex(_)} unpack 'x68A2x8A2x8A2x8A2x8A2', regs
            #     #         if (tSunDir[x] & 0x70) {
            #     #             args[x] = 0x0180
            #     #         } else {
            #     #             args[x] = 0x0100
            #     #         }
            #     #     }
            #     # }
            # }
            #
            # for (my c = 0; c<wCmds{cmd}{count}; c++) {
            #     pad = 0
            #
            #     if (wCmds{cmd}{size} == 4) {
            #         pad = int(c / 2)*2
            #         pad = c if (cmd =~ m/^triggerSun.*/)
            #     }
            #     regStart = (wCmds{cmd}{reg} * 10 + wCmds{cmd}{byte} + pad + c * wCmds{cmd}{size} )*2
            #
            #     reg = hex(substr(regs, regStart, wCmds{cmd}{size} * 2))
            #
            #     if((args[c] =~ m/^[-\d]+/) and (args[c] >=    wCmds{cmd}{min}) and (args[c] <=    wCmds{cmd}{max})) {
            #         reg &= ~(wCmds{cmd}{mask})
            #         reg |= wCmds{cmd}{enable}
            #         reg |= ((args[c] +    wCmds{cmd}{offset})<<wCmds{cmd}{shift}) & wCmds{cmd}{mask} 
            #
            #     } elsif ((args[c] == "off") and (wCmds{cmd}{enable} > 0)) {
            #         reg &= ~(wCmds{cmd}{enable})
            #
            #     } elsif ((args[c] == "on") and (wCmds{cmd}{min} == 0) and (wCmds{cmd}{max} == 0)) {
            #         reg |= wCmds{cmd}{enable}
            #
            #     } else {
            #         return "wrong argument ".args[c]
            #
            #     }
            #
            #     size = wCmds{cmd}{size}*2
            #
            #     substr(regs, regStart ,size, sprintf("0".size."x",reg))
            #
            # }
            #
            # @regsA = unpack('(A20)*', regs)
            #
            # readingsBeginUpdate(hash)
            # for(my x=0; x<8; x++)    {
            #     readingsBulkUpdate(hash, ".regx", regsA[x], 0)
            #     #readingsBulkUpdate(hash, "regx", regsA[x], 0)
            # }
            # readingsBulkUpdate(hash, "configModified", 1, 0)
            # readingsEndUpdate(hash, 1)
            #
            # DUOFERN_DecodeWeatherSensorConfig(hash)
            # return undef

        elif cmd in commands:
            logger.info("command valid")
            subCmd = None
            chanNo = "01"
            argV = "00"
            argW = "0000"
            timer = "00"
            buf = duoCommand
            command = None

            if 'chanNo' in self.modules['by_code'][code]:
                chanNo = self.modules['by_code'][code]['chanNo']
            # chanNo = hash->{chanNo} if (hash->{chanNo})

            if 'noArg' in commands[cmd]:
                if (arg and (arg == "timer")):
                    timer = "01"
                subCmd = "noArg"
                argV = "00"

            elif 'value' in commands[cmd]:
                if (arg2 and (arg2 == "timer")):
                    timer = "01"
                if arg is None:
                    return "Missing argument"
                if (int(arg) < 0 or int(arg) > 100):
                    raise Exception("Wrong argument arg")
                subCmd = "value"
                argV = "%02x" % arg

            elif 'value2' in commands[cmd]:
                if arg is None:
                    return "Missing argument"
                if int(arg) < 0 or int(arg) > 3200:
                    raise Exception("Wrong argument arg")
                subCmd = "value2"
                argW = "%04x" % (arg * 10)

            elif 'value3' in commands[cmd]:
                maxArg = 150
                if code[0:2] == "48":
                    maxArg = 255
                if arg2 and (arg2 == "timer"):
                    timer = "01"
                if arg is None:
                    return "Missing argument"
                if int(arg) < 0 or int(arg) > maxArg:
                    raise Exception("Wrong argument arg")
                subCmd = "value3"
                argV = "%02x" % arg

            elif 'value4' in commands[cmd]:
                if arg2 and (arg2 == "timer"):
                    timer = "01"
                if arg is None:
                    return "Missing argument"
                if int(arg) < 0 or int(arg) > 5000:
                    raise Exception("Wrong argument arg")
                arg = arg / 100
                subCmd = "value4"
                argV = "%02x" % arg

            elif 'temp1' in commands[cmd]:
                if arg is None:
                    return "Missing Argument"
                if int(arg) < -40 or int(arg) > 80:
                    return "Wrong argument {}".format(arg)

                # return "Missing argument" if (!defined(arg))
                # return "Wrong argument arg" if (arg !~ m/^\d+(\.\d+|)/ || arg < -40 || arg > 80)
                subCmd = "temp1"
                argW = "%04x" % ((arg * 10) + 400)

            elif 'temp2' in commands[cmd]:
                if arg is None:
                    return "Missing Argument"
                if int(arg) < -40 or int(arg) > 80:
                    return "Wrong argument {}".format(arg)
                subCmd = "temp2"
                argV = "%02x" % ((arg * 2) + 80)

            else:
                if arg is None:
                    return "Missing Argument"
                if (arg2 and (arg2 == "timer")):
                    timer = "01"
                subCmd = arg
                argV = "00"

            if subCmd not in commands[cmd]:
                raise Exception("Wrong argument {}, {}".format(arg, subCmd))

            position = -1 if not "position" in self.modules['by_code'][code] else self.modules['by_code'][code][
                "position"]
            # toggleUpDown    = AttrVal(name, "toggleUpDown", "0")
            toggleUpDown = self.modules['by_code'][code]['toggleUpDown'] if 'toggleUpDown' in self.modules['by_code'][
                code] else 0
            moving = "stop" if not "moving" in self.modules['by_code'][code] else self.modules['by_code'][code][
                "moving"]
            timeAutomatic = "on" if not "timeAutomatic" in self.modules['by_code'][code] else \
                self.modules['by_code'][code]["timeAutomatic"]
            dawnAutomatic = "on" if not "dawnAutomatic" in self.modules['by_code'][code] else \
                self.modules['by_code'][code]["dawnAutomatic"]
            duskAutomatic = "on" if not "duskAutomatic" in self.modules['by_code'][code] else \
                self.modules['by_code'][code]["duskAutomatic"]

            if moving != "stop":
                if cmd in ('up', 'down', 'toggle'):
                    if toggleUpDown:
                        cmd = "stop"
            # self.update_state(code,"moving","moving")

            if ((cmd == "toggle") and (position > -1)):
                self.update_state(code, "moving", "moving", 1)
            if ((cmd == "dawn") and (dawnAutomatic == "on") and (position > 0)):
                self.update_state(code, "moving", "up", 1)
            if ((cmd == "dusk") and (duskAutomatic == "on") and (position < 100) and (position > -1)):
                self.update_state(code, "moving", "down", 1)

            if timer == "00" or timeAutomatic == "on":
                if ((cmd == "up") and (position > 0)):
                    self.update_state(code, "moving", "up", 1)
                if ((cmd == "down") and (position < 100) and (position > -1)):
                    self.update_state(code, "moving", "down", 1)

            if cmd == "position":
                if arg > position:
                    self.update_state(code, "moving", "down", 1)
                elif (arg < position):
                    self.update_state(code, "moving", "up", 1)
                else:
                    self.update_state(code, "moving", "stop", 1)

            command = commands[cmd][subCmd]

            buf = buf.replace("yyyyyy", code)
            buf = buf.replace("nnnnnnnnnnnnnnnnnnnn", command)
            buf = buf.replace("nn", argV)
            buf = buf.replace("tt", timer)
            buf = buf.replace("wwww", argW)
            buf = buf.replace("kk", chanNo)
            logger.debug("trying to send {}".format(buf))
            yield from self.send(buf)
            #            if ('device' in self.modules['by_code'][code]):
            # hash = defs{hash->{device}}

        else:
            raise Exception("command {} not found".format(cmd))


# return SetExtensions(hash, list, @b)

if __name__ == "__main__":
    formatter = logging.Formatter('%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s')
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
