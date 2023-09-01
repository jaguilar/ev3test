#!/usr/bin/env pybricks-micropython

from pybricks.hubs import EV3Brick
from pybricks.ev3devices import (
    Motor,
    TouchSensor,
    ColorSensor,
    InfraredSensor,
    UltrasonicSensor,
    GyroSensor,
)
from pybricks.parameters import Port, Stop, Direction, Button, Color
from pybricks.tools import wait, StopWatch, DataLog
from pybricks.robotics import DriveBase
from pybricks.media.ev3dev import SoundFile, ImageFile
from pybricks.tools import wait
from pybricks.messaging import BluetoothMailboxServer, TextMailbox
import _thread



server = BluetoothMailboxServer()
mbox = TextMailbox('greeting', server)
server.wait_for_connection(1)
print('connected')

mbox.wait()
msg = mbox.read()
print(msg)
mbox.send('pong')
