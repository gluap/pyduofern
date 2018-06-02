#!/usr/bin/env python3
# coding=utf-8
#   python interface for dufoern usb stick
#   Copyright (C) 2017 Paul Görgen
#   Rough python re-write of the FHEM duofern modules by telekatz, also licensed under GPLv2
#   This re-write contains only negligible amounts of original code
#   apart from some comments to facilitate translation of the not-yet
#   translated parts of the original software. Modification dates are
#   documented as submits to the git repository of this code, currently
#   maintained at https://bitbucket.org/gluap/pyduofern.git

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
import tempfile

import pytest

from pyduofern.duofern_stick import hex

# pytestmark = pytest.mark.asyncio

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

import pyduofern.duofern_stick  # import DuofernStickAsync


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
        pass

    @classmethod
    def readin(cls, replayfile):
        f = open(replayfile, 'r')
        lines = f.readlines()
        actions = [l.split(" ") for l in lines]
        actions.reverse()
        return actions

    def next_line(self):
        return self.replay.pop()

    def next_is_received(self):
        if not self.replay: return False
        return self.replay[-1][0] != "sent"

    def write(self, data):
        logger.warning("writing {} detected by mock writer".format(data))
        if self.next_is_received():
            self.finished_actions.append("recording states next command was send but we received something")
        line = self.next_line()[1]
        if bytearray.fromhex(line.strip()) != data:
            self.finished_actions.append("\nrecording states we sent {} but we are sending {}".format(line, hex(data)))
        else:
            self.finished_actions.append("OK")
        while self.next_is_received():
            line = self.next_line()[1].strip()
            try:
                self.proto.data_received(bytearray.fromhex(line))
                self.finished_actions.append("OK")
            except Exception:
                self.finished_actions.append("EXCEPTION WHILE REPLAYING RECIEVED MESSAGE")
            self.proto._ready.set()


@pytest.mark.parametrize('replayfile', list_replays())
@pytest.mark.asyncio
def test_init_against_mocked_stick(event_loop, replayfile):
    proto = pyduofern.duofern_stick.DuofernStickAsync(event_loop, system_code="ffff",
                                                      config_file_json=tempfile.mktemp(),
                                                      recording=False)
    proto.transport = TransportMock(proto, replayfile)
    proto._ready = asyncio.Event()

    init_ = asyncio.async(proto.handshake())

    proto._ready.set()

    result = yield from init_

    assert ["OK"] * len(
        proto.transport.finished_actions) == proto.transport.finished_actions, "some sends did not match" \
                                                                               "the recording"
    proto.send_loop.cancel()
