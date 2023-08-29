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

arm1 = Motor(Port.C)
arm2 = Motor(Port.D)

class EWMA:
    def __init__(self, start, alpha):
        self._avg = start
        self._alpha = alpha

    def point(self, data):
        self._avg = self._avg * (1.0-self._alpha) + self._alpha * data
        return self._avg


def low_torque_run_until_stalled(motor: Motor, speed: int, torque: int = 40):
    motor.stop()
    before_limits = motor.control.limits()
    motor.control.limits(None, None, torque)

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



if False:

    arm1_throw = -1
    arm2_throw = -1
    brick.speaker.set_volume(10)


    def calibrate_task():
        num_left_button_presses = 0
        while True:
            if False:
                while num_left_button_presses < 10:
                    if Button.LEFT in brick.buttons.pressed():
                        num_left_button_presses += 1
                    else:
                        num_left_button_presses = 0
                    await wait(100)
            calibrate()
            break


    def calibrate():
        global calibrating
        calibrating = True

        brick.speaker.beep()

        # Wait for the user to pick up their finger.
        while Button.LEFT in brick.buttons.pressed():
            wait(50)

        arm1.stop()
        arm2.stop()

        a1low, a1high, a2low, a2high = arm1.angle(), arm1.angle(), arm2.angle(), arm2.angle()

        arm1.run(1)

        # Begin watching the arms. Record their upper and lower extremes. If the left button gets pressed again we exit.
        while not Button.LEFT in brick.buttons.pressed():
            a1 = arm1.angle()
            a2 = arm2.angle()
            if a1 < a1low: a1low = a1
            if a1 > a1high: a1high = a1
            if a2 < a2low: a2low = a2
            if a2 > a2high: a2high = a2

            print(a1low, a1high, a2low, a2high)

            await wait(200)

        # Okay, we know the extremes of each motor. Let's re-home the angle of each motor so zero is the lower extreme.
        global arm1_throw, arm2_throw
        arm1_throw = reset_angle_from_extremes(arm1, a1low, a1high)
        arm2_throw = reset_angle_from_extremes(arm2, a2low, a2high)

        # Finally, set the arms to a known good neutral position. (Known by me, the programmer lol)
        brick.speaker.beep()

        print(arm1.angle(), arm1_throw)
        print(arm2.angle(), arm2_throw)

        arm1_target = 90
        arm2_target = 120
        # await my_run_target(arm1, 1, arm1_target)
        # print('finished arm1 target')
        await my_run_target(arm2, 1, arm2_target)
        print('finished arm2 target')
        brick.speaker.beep()



    def reset_angle_from_extremes(motor: Motor, low: int, high: int):
        motor.reset_angle(motor.angle() - low)
        return high - low







    # run_task(calibrate_task())

    if False:
        async def my_run_target(motor: Motor, speed: int, target: int):
            brick.speaker.beep()
            diff = target - motor.angle()
            mspeed = speed if diff > 0 else -speed

            print(mspeed, diff)
            motor.run(mspeed)

            while abs(motor.angle() - target) > 2:
                await wait(100)


        async def test_run_target(motor: Motor):
            await my_run_target(motor, 1, 35)

        run_task(test_run_target(arm2))

    arm1.stop()
    arm2.stop()
    arm2.control.limits(None, None, 10)
    arm2.run_until_stalled(75)
    while not arm2.stalled():
        wait(25)
    brick.speaker.beep()
