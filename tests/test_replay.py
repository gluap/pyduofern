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
import os
import re
import tempfile
import traceback
import time
import sys
from ast import literal_eval

import pytest

from pyduofern.duofern_stick import hex

# pytestmark = pytest.mark.asyncio

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

from pyduofern.duofern_stick import DuofernStickAsync


# @pytest.fixture  # (scope="function", params=[True, False])
# def looproto(event_loop):
#    loop = event_loop

# proto =
# return loop, proto


def list_replays():
    replaydir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'replaydata')
    files = os.listdir(replaydir)
    return [os.path.join(replaydir, f) for f in files]


class TransportMock:
    def __init__(self, proto, replayfile):
        super(TransportMock).__init__()
        self.proto = proto
        self.unittesting = True
        self.replay = self.readin(replayfile)
        self.finished_actions = []
        self.receiveloop = asyncio.ensure_future(self.receive_loop())
        pass

    @classmethod
    def readin(cls, replayfile):
        f = open(replayfile, 'r')
        lines = f.readlines()
        lines = ["!" + l for l in lines if l[0] != "?"]
        actions = [l.split(" ") for l in lines]
        actions.reverse()
        return actions

    def next_line(self):
        return self.replay.pop()

    def next_is_received(self):
        if not self.replay: return False
        return self.replay[-1][0][1:] == "received"

    def next_is_action(self):
        if not self.replay: return False
        return self.replay[-1][0][1:] == "sending_command"

    def next_optional(self):
        if not self.replay: return False
        return self.replay[-1][0][0] == "?"

    def write(self, data):
        optional = self.next_optional()
        result = self.check_if_next_matches(data)
        if (result != "OK") and not optional:
            self.finished_actions.append(result)  # pragma: no cover
        else:
            self.finished_actions.append("OK")

    #  await asyncio.ensure_future(self.receive())

    async def receive_loop(self):
        while self.replay:
            await asyncio.sleep(0.01)
            if self.next_is_received():
                line = self.next_line()[1].strip()
                try:
                    if self.proto is None:
                        print("lol")
                    self.proto.data_received(bytearray.fromhex(line))
                    self.finished_actions.append("OK")
                except Exception as exc:  # pragma: no cover
                    traceback_str = ''.join(traceback.format_tb(exc.__traceback__))
                    self.finished_actions.append(f"EXCEPTION WHILE REPLAYING RECIEVED MESSAGE {exc}, {traceback_str}")
                    logging.exception("exception I found!", exc_info=True)

    async def actions(self):
        while self.next_is_action():
            await asyncio.sleep(0.01)
            command_args = " ".join(self.next_line()[1:])
            args_and_kwargs = re.match(r"(\([^\)]+\)).*({[^}]+})", command_args)
            args, kwargs = args_and_kwargs.groups()
            self.proto.command(*literal_eval(args),**literal_eval(kwargs))
            await asyncio.sleep(0.01)

    def check_if_next_matches(self, data):
        logger.warning("writing {} detected by mock writer".format(data))
        msg = ""
        if self.next_is_received():
            msg += "recording states next command was send but we received something"  # pragma: no cover
        line = self.next_line()[1]
        if bytearray.fromhex(line.strip()) != data:
            return msg + "\nrecording states we sent {} but we are sending {}".format(line,
                                                                                      hex(data))  # pragma: no cover
        else:
            return "OK"


@pytest.mark.parametrize('replayfile', list_replays())
@pytest.mark.asyncio
async def test_init_against_mocked_stick(event_loop, replayfile):
    proto = DuofernStickAsync(event_loop, system_code="ffff", config_file_json=tempfile.mktemp(), recording=False)
    proto.transport = TransportMock(proto, replayfile)
    proto._ready = asyncio.Event()

    init_ = asyncio.ensure_future(proto.handshake())

    proto._ready.set()

    await init_
    assert ["OK"] * len(
        proto.transport.finished_actions) == proto.transport.finished_actions, "some sends did not match" \
                                                                               "the recording"

    await asyncio.wait_for(proto.available, 1)

    # if proto.transport.next_is_sent():
    #    proto.transport.write(bytearray.fromhex(proto.transport.replay[-1][1].strip()))
    start_time = time.time()
    async def feedback_loop():
        while proto.transport.replay:
            await asyncio.sleep(0)
            if time.time() - start_time > 3 and sys.gettrace() is None:
                raise TimeoutError("Mock test should not take longer than 3 seconds, asynchronous loop must be stuck"
                                   "Be aware this is not raised in debug mode.")

            if proto.transport.next_is_action():
                asyncio.ensure_future(proto.transport.actions())
                print("bla")

    await feedback_loop()
    proto.transport.receiveloop.cancel()

    proto.send_loop.cancel()
