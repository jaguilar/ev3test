#!/usr/bin/env pybricks-micropython

import math

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
from pybricks.messaging import BluetoothMailboxServer, Mailbox
from micropython import const
import ustruct
from typing import *
import _thread
import net_formats

brick = EV3Brick()
calibrating = False

turntable = Motor(Port.A)
arm1 = Motor(Port.B, gears=[8, 40], positive_direction=Direction.COUNTERCLOCKWISE)
arm2 = Motor(Port.C, gears=[[8, 36], [12, 36]], positive_direction=Direction.CLOCKWISE)
turntable_limit_switch = TouchSensor(Port.S1)

turntable_range = [0, 0]
turntable_min_speed = 15
arm1_range = [0, 0]
arm1_min_speed = int(15 / (40 / 8))
arm2_range = [0, 0]
arm2_min_speed = int(100 / ((36.0 / 8.0) * (36 / 12)))

# Geometry notes:
#
# Modelling in a right handed coordinate system:
# * X increases to the right.
# * Y increases going up.
# * Z increases "toward" you, or to the right of X.
#
# All measurements are with the model facing to the right.
#
# Turntable rotation: 180 degrees.
# Turntable 0: half way between limits.
# Turntable positive direction: clockwise looking from above,
# i.e. +rotation causes arm to point toward increasing Z.
#
# Arm 1 height: 12
# Arm 1 offset from turntable: +2 in the direction of the arm.
# Arm 1 length: 20
# Arm 2 length: 15
#
# Arm rotation measurements: 0 degrees = pointing straight up.
# Increasing arm rotation rotates clockwise.
#
# Arm 1 min: 17 degrees
# Arm 1 max: 90 degrees (approx horizontal, artificial limit, not calibrated at the moment)
# Arm 2 min: -6 degrees (can bend slightly further than straight up)
# Arm 2 max: 161 degrees
#
# Calibrated degrees will not match the exact number of degrees, so to get
# correct movement we have to scale all motor movements accordingly.


def calibrate_arm1_raise():
    arm1.run_until_stalled(-3 * arm1_min_speed, then=Stop.COAST, duty_limit=20)
    arm1.reset_angle(17)
    arm1_range[0] = 17
    arm1_range[1] = 90


def calibrate_arm2():
    # Runs while arm1 is pointing up, so it should be safe to test our whole limit.
    arm2.run_until_stalled(-4 * arm2_min_speed, duty_limit=35)
    arm2.reset_angle(-6)
    arm2_range[0] = -6
    arm2.run_until_stalled(4 * arm2_min_speed, duty_limit=35)
    arm2_range[1] = arm2.angle()


def calibrate_turntable():
    turntable_limits = turntable.control.limits()
    turntable.stop()
    turntable.control.limits(turntable_limits[0], turntable_limits[1], 60)
    turntable.run(turntable_min_speed)

    while not turntable_limit_switch.pressed():
        wait(10)

    turntable.brake()
    turntable.reset_angle(90)
    turntable_range[1] = 90

    turntable.stop()
    turntable.control.limits(*turntable_limits)

    turntable.run_until_stalled(-3 * turntable_min_speed, duty_limit=40)
    turntable_range[0] = turntable.angle()


def send_motor(
    m: Motor, min_speed: int, range: Tuple[int, int], target: int, time_ms: int
):
    """Tells a motor to go to the given target position at a target time.

    Each motor has an associated min_speed and range. The min_speed is
    the *slowest* the motor is allowed to move. This is because some EV3
    motors, especially the medium motor, have erratic behavior at lower speeds.
    The range is the calibrated minimum and maximum angle value for the motor.
    Requests for targets outside the range will instead be set to the range limit
    instead.
    """
    actual_target = max(range[0], min(range[1], target))
    ideal_speed = 1000 * float(abs(actual_target - m.angle())) / time_ms
    actual_speed = max(ideal_speed, min_speed)
    m.run_target(actual_speed, actual_target, wait=False)


def send_turntable(target: int, time_ms: int):
    send_motor(turntable, turntable_min_speed, turntable_range, target, time_ms)


def send_arm1(target: int, time_ms: int):
    send_motor(arm1, arm1_min_speed, arm1_range, target, time_ms)


def send_arm2(target: int, time_ms: int):
    send_motor(arm2, arm2_min_speed, arm2_range, target, time_ms)


calibrate_arm1_raise()
send_arm1(arm1_range[0] + 10, 2000)
calibrate_arm2()
send_arm2(arm2_range[0] + 20, 2000)
calibrate_turntable()
send_turntable(0, 2000)

print(turntable_min_speed, arm1_min_speed, arm2_min_speed)
print(turntable_range, arm1_range, arm2_range)


send_turntable(45, 500)
print("turntable_sent")
send_arm1(50, 500)
print("arm1_sent")
send_arm2(10, 500)
print("arm2_sent")
print(turntable.angle(), arm1.angle(), arm2.angle())


server = BluetoothMailboxServer()
print('waiting for connection')
server.wait_for_connection(1)
print('connected')


def update_positions():
    """Thread for periodically updating the current_position mailbox."""
    position_mailbox = Mailbox(net_formats.current_channel, server)

    _UPDATE_FREQ_MS = const(33)

    while True:
        position_mailbox.send(ustruct.pack(net_formats.current_format, turntable.angle(), arm1.angle(), arm2.angle()))
        wait(_UPDATE_FREQ_MS)




def send_ranges():
    range_mailbox = Mailbox(net_formats.range_channel, server)
    range_mailbox.wait()  # Client will tell us when they are ready for a message.
    print('got ready message from client')
    buffer = ustruct.pack(
        net_formats.range_format,
        turntable_range[0],
        turntable_range[1],
        arm1_range[0],
        arm1_range[1],
        arm2_range[0],
        arm2_range[1],
    )
    range_mailbox.send(buffer)
    print('sent ranges')


def receive_position_commands():
    mailbox = Mailbox(net_formats.target_channel, server)

    _FORMAT = "!hhhh"  # time_to_target, turntable, arm1, arm2

    while True:
        mailbox.wait_new()
        (
            time_to_target,
            turntable_target,
            arm1_target,
            arm2_target,
        ) = ustruct.unpack_from(net_formats.target_format, mailbox.read())
        print('Got new target: in ', time_to_target, 'ms: ', turntable_target, arm1_target, arm2_target)

        send_turntable(turntable_target, time_to_target)
        send_arm1(arm1_target, time_to_target)
        send_arm2(arm2_target, time_to_target)


_thread.start_new_thread(receive_position_commands, tuple())
_thread.start_new_thread(update_positions, tuple())

send_ranges()

print('main thread sleeping forever')
while True:
    wait(5000)
