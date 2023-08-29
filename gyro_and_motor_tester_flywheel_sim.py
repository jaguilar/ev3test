#!/usr/bin/env pybricks-micropython

import math

from pybricks.hubs import EV3Brick
from pybricks.ev3devices import (Motor, TouchSensor, ColorSensor,
                                 InfraredSensor, UltrasonicSensor, GyroSensor)
from pybricks.parameters import Port, Stop, Direction, Button, Color
from pybricks.tools import wait, StopWatch, DataLog
from pybricks.robotics import DriveBase
from pybricks.media.ev3dev import SoundFile, ImageFile

# This program requires LEGO EV3 MicroPython v2.0 or higher.
# Click "Open user guide" on the EV3 extension tab for more information.


# Create your objects here.
ev3 = EV3Brick()

motor = Motor(port=Port.A)

gyro = GyroSensor(Port.S1)

# The motor is going to pretend to be a wheel spinning freely.
# We want to reduce the speed of the motor by 10% in the first second after
# we stop receiving input. From that, we can calculate the drag factor.
#
# Drag equation is
#
# D = coefficient * v^2
#
# I think technically this requires integrals to solve? something like
#
# 300^2 - 270^2 = integral(v=[270,300], coefficient * v^2), solve for
# coefficient
#
# 17100 = integral(v=[270,300], v^2) * coefficient
#         [v=[270,300]] v^3/3 * coefficient
# 17100 = 2439000 * coefficient
# coefficient = 17100 / 2439000
# coefficient = 0.07

drag_coefficient = 0.004


stopwatch = StopWatch()
stopwatch.resume()
speed = 0.0
time_step = 10
second_frac = time_step / 1000.
while True:
  stopwatch.reset()
  if speed < 1:
    speed = 0

  if speed > 0:
    # Apply drag:
    v2 = speed ** 2
    drag = v2 * drag_coefficient
    new_energy = v2 - drag
    new_speed = math.sqrt(new_energy)
    speed = new_speed

  gyro_speed = gyro.speed() or 0
  if (gyro_speed > 0):
    speed += gyro_speed * second_frac
    print(speed)

  if speed > 600:
    print('Capping speed at 300')
    speed = min(300, speed)

  motor.run(speed)

  # Wait until the end of a 10ms interval.
  wait(max(0, time_step - stopwatch.time()))






