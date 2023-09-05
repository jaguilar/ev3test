#!/usr/bin/env python3
from pybrickspc.messaging import BluetoothMailboxClient, Mailbox
import net_formats
import struct
import sys


if __name__ == '__main__':
    print('I think you meant to run client_test.py or something else.')
    sys.exit(1)

# This is the address of the server EV3 we are connecting to.
SERVER = "f0:45:da:13:1c:8a"

_mailbox_client = BluetoothMailboxClient()

print("establishing connection...")
_mailbox_client.connect(SERVER)
print("connected!")


_current_position_mbox = Mailbox(net_formats.current_channel, _mailbox_client)
_target_position_mbox = Mailbox(net_formats.target_channel, _mailbox_client)
_ranges_mbox = Mailbox(net_formats.range_channel, _mailbox_client)


def ranges():
    _ranges_mbox.send(struct.pack('!h', 1))
    print('waiting for ranges')
    _ranges_mbox.wait()
    print('got ranges')
    return struct.unpack_from(net_formats.range_format, _ranges_mbox.read())


def current_position():
    print('waiting for position')
    _current_position_mbox.wait()
    print('got position')
    return struct.unpack_from(_current_position_mbox, _current_position_mbox.read())


def set_target(ms_from_now: int, turntable_angle: int, arm1_angle: int, arm2_angle: int):
    print('sending ', ms_from_now, turntable_angle, arm1_angle, arm2_angle)
    _target_position_mbox.send(struct.pack(net_formats.target_format, ms_from_now, turntable_angle, arm1_angle, arm2_angle))
