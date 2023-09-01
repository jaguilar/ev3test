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


class MyScalingMotor:
    def __init__(self, motor: Motor, scale: float):
        self.motor = motor
        self._scale = float(scale)


    def angle(self):
        return self.motor.angle() / self._scale


    def run(self, speed):
        return self.motor.run(self._scale * speed)


    def run_angle(self, speed, angle, **kwargs):
        return self.motor.run_angle(self._scale*speed, self._scale*angle, **kwargs)


    def run_target(self, speed, target, **kwargs):
        print(self._scale * speed, self._scale * target, kwargs)
        return self.motor.run_target(self._scale * speed, self._scale * target, **kwargs)


    def reset_angle(self, new_angle):
        return self.motor.reset_angle(new_angle * self._scale)


    def stop(self):
        return self.motor.stop()


turn = Motor(Port.B)
arm1 = MyScalingMotor(Motor(Port.C), scale=(40.0/12))
arm2 = MyScalingMotor(Motor(Port.D, positive_direction=Direction.COUNTERCLOCKWISE), scale=(20.0/12))


class EWMA:
    def __init__(self, start, alpha):
        self._avg = start
        self._alpha = alpha

    def record(self, data):
        self._avg = self._avg * (1.0-self._alpha) + self._alpha * data

    def avg(self):
        return self._avg


def calibrate_throw(motor: Motor, speed: float, torque_fraction: int = 40):
    motor.stop()
    before_limits = motor.motor.control.limits()
    motor.motor.control.limits(before_limits[0], before_limits[1], torque_fraction)

    target_ms_per_degree = abs(1000.0 / speed)
    stalled_ms_per_degree = target_ms_per_degree * 2
    quit_ms_per_degree = max(100, target_ms_per_degree * 3)
    avg_ms_per_degree = EWMA(target_ms_per_degree, 0.2)

    motor.run(speed)
    wait(100)
    angle_before = motor.angle()

    watch = StopWatch()
    watch.resume()
    while True:
        wait(50)
        angle_after = motor.angle()
        if angle_after != angle_before:
            diff = 1.0 * abs(angle_after - angle_before)
            ms_per_angle = watch.time() / diff
            for x in range(int(diff)):
                avg_ms_per_degree.record(ms_per_angle)
            watch.reset()

        print(watch.time())
        if watch.time() > quit_ms_per_degree:
            print('had to quit took too long to get degree: ', watch.time(), ' > ', quit_ms_per_degree)
            break
        if avg_ms_per_degree.avg() > stalled_ms_per_degree:
            print('had to quit average fell too low: ', avg_ms_per_degree.avg(), ' > ', stalled_ms_per_degree)
            break

        angle_before = angle_after

    motor.stop()
    motor.motor.control.limits(*before_limits)


arm1_calib_speed = 10
arm1_throw = 90
arm2_calib_speed = 40
arm2_throw = 60

# For a given input degree, we have to set

# Arm 2 has a 8:1 reduction. A speed of 50 seems precise enough.
print(calibrate_throw(arm2, arm2_calib_speed, torque_fraction=100))
arm2.run_angle(5, -10, then=Stop.HOLD, wait=True)
arm2.reset_angle(-30)  # We start at -30 degrees from straight up.

# Arm 1 has a 36:20 reduction. This is about a 2:1 ratio and thus we'll reduce the speed by a factor of 4.
print(calibrate_throw(arm1, arm1_calib_speed))
arm1.reset_angle(0)  # We start pointing straight up.

arm1.run_target(20, -45, then=Stop.HOLD, wait=True)
arm1.run_target(20, -90, then=Stop.HOLD, wait=True)
arm1.run_target(20, -22.5, then=Stop.HOLD, wait=True)
arm1.run_target(20, -45-22.5, then=Stop.HOLD, wait=True)
arm2.run_target(20, -60, then=Stop.HOLD, wait=True)
arm2.run_target(20, -45, then=Stop.HOLD, wait=True)
arm2.run_target(20, -90, then=Stop.HOLD, wait=True)
arm2.run_target(20, -75, then=Stop.HOLD, wait=True)

arm1.stop()
arm2.stop()
