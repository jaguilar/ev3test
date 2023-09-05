# /usr/bin/env python3

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

from math import sin, cos, radians
import numpy as np
from numpy.linalg import norm
from numpy.typing import NDArray
from typing import Annotated, Literal, TypeVar
from scipy.optimize import minimize

_r1 = 2.0
_l2 = 20.0
_l3 = 15.0

Vec3 = Annotated[NDArray[np.generic], Literal[3]]

def get_radius(input: Vec3) -> np.floating:
    return _r1 + _l2 * sin(input[1]) + _l3 * sin(input[1] + input[2])


def get_pos(input: Vec3) -> Vec3:
    """Finds the X,Y,Z vector given the settings of each motor. The settings of the motors are given in radians from their neutral positions."""
    ar = input[0]
    a2 = input[1]
    a3 = input[2]

    r = get_radius(input)

    x = r * cos(ar)
    y = _l2 * cos(a2) + _l3 * cos(a2 + a3)
    z = r * sin(ar)
    ret = np.array((x, y, z))
    print(input, ret)
    return ret


def get_err(input:Vec3, target: Vec3) -> np.floating:
    return norm(target - get_pos(input))


def get_motor_settings(target: Vec3):
    return minimize(get_err, (0, 0, 0), args=(target,), method="slsqp", jac="3-point", bounds=((radians(-90), radians(90)), (radians(17), radians(90)), (radians(-6), radians(161))))




