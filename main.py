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
import _thread

brick = EV3Brick()
calibrating = False

turn = Motor(Port.B)
arm1 = Motor(Port.C)
arm2 = Motor(Port.D)


class EWMA:
    def __init__(self, start, alpha):
        self._avg = start
        self._alpha = alpha

    def point(self, data):
        self._avg = self._avg * (1.0-self._alpha) + self._alpha * data
        return self._avg


def low_torque_run_until_stalled(motor: Motor, speed: int, torque_fraction: int = 40):
    motor.stop()
    before_limits = motor.control.limits()
    motor.control.limits(None, None, torque_fraction)

    # Begin rotating the motor until an exponentially-weighted moving average shows its speed has fallen below half the desired rate.
    time_for_five_degrees = 5 * (1000 / abs(speed))

    ewma = EWMA(5, 0.2)
    angle_before = motor.angle()
    motor.run(speed)
    while True:
        wait(time_for_five_degrees)
        angle_after = motor.angle()
        avg = ewma.point(abs(angle_after - angle_before))
        if avg < 1:
            break
        angle_before = angle_after
    motor.stop()
    motor.control.limits(*before_limits)


def calibrate_throw(motor: Motor, speed: int):
    low_torque_run_until_stalled(motor, speed)
    high = motor.angle()
    print(high)
    low_torque_run_until_stalled(motor, -speed)
    low = motor.angle()
    print(low)
    target = (high + low) / 2
    print(target)
    motor.run_target(speed * 3, target)
    return (low, high)

# Arm 2 has a 8:1 reduction. A speed of 50 seems precise enough.
print(calibrate_throw(arm2, 50))
# Arm 1 has a 36:20 reduction. This is about a 2:1 ratio and thus we'll reduce the speed by a factor of 4.
print(calibrate_throw(arm1, 12.5))


brick.speaker.beep()
