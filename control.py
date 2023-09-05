#! /usr/bin/env python3

import client
import kinematics
import numpy as np
from numpy.linalg import norm
from math import degrees, radians
import pygame




def input_gain(x: float):
    return 0.4 * x + 0.6 * x**3


# joystick 0: negative=-x positive=+x
# joystick 1: negative=-z positive=+z
# joystick 3: negative=+y positive=-y
# button 0: save pos
# button 2: replay positions
# button 3: clear positions
_MAX_MOVEMENT = 1


def get_x(j: pygame.joystick.JoystickType):
    return input_gain(j.get_axis(0)) * _MAX_MOVEMENT


def get_y(j: pygame.joystick.JoystickType):
    return input_gain(-j.get_axis(3)) * _MAX_MOVEMENT


def get_z(j: pygame.joystick.JoystickType):
    return input_gain(j.get_axis(1)) * _MAX_MOVEMENT


def get_arm_direction(j: pygame.joystick.JoystickType):
    raw = np.array((get_x(j), get_y(j), get_z(j)))
    mag = linalg.norm(raw)
    if mag > _MAX_MOVEMENT:
        raw *= mag / _MAX_MOVEMENT
    return raw


_RANGES = client.ranges()

_turntable_true_throw = 180
_turntable_scale = (_RANGES[1] - _RANGES[0]) / _turntable_true_throw
_arm1_true_throw = 73
_arm1_scale = (_RANGES[3] - _RANGES[2]) / _arm1_true_throw
_arm2_true_throw = 167
_arm2_scale = (_RANGES[5] - _RANGES[4]) / _arm2_true_throw


def turntable_raw_to_logical(angle: float):
    # 90 is the reference point for the turntable, so we scale the difference between 90 and the computed
    # minimum.
    diff = 90 - angle
    return 90 - diff / _turntable_scale


def turntable_logical_to_raw(angle: float):
    diff = 90 - angle
    return 90 - diff * _turntable_scale


def arm1_raw_to_logical(angle: float):
    # 17 is the reference point for arm1, and it is also the minimum
    diff = angle - 17
    return 17 + diff / _arm1_scale


def arm1_logical_to_raw(angle: float):
    # 17 is the reference point for arm1, and it is also the minimum
    diff = angle - 17
    return 17 + diff * _arm1_scale


def arm2_raw_to_logical(angle: float):
    # -6 is the reference point for arm2, and it is also the minimum.
    diff = angle - (-6)
    return (-6) + diff / _arm2_scale


def arm2_logical_to_raw(angle: float):
    # 17 is the reference point for arm2, and it is also the minimum
    diff = angle - (-6)
    return -6 + diff * _arm2_scale


def get_current_angles():
    (r1, r2, r3) = client.current_position()
    return (turntable_raw_to_logical(r1), arm1_raw_to_logical(r2), arm2_raw_to_logical(r3))


def set_target_angles(v: np.ndarray, in_ms: int = 500):
    r1, r2, r3 = v[0], v[1], v[2]
    client.set_target(in_ms, int(turntable_logical_to_raw(r1)), int(arm1_logical_to_raw(r2)), int(arm2_logical_to_raw(r3)))


print('pygame init')
pygame.init()
print('pygame init done')

def main():
    # Used to manage how fast the screen updates.
    clock = pygame.time.Clock()
    prev_dir = None

    while True:
        if pygame.joystick.get_count() == 0:
            # Don't do anything unless there is a joystick
            clock.tick(1)
            print('no joy')
            continue

        joysticks = [
            pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())
        ]
        button_list = [
            event.button
            for event in pygame.event.get()
            if event.type == pygame.JOYBUTTONDOWN
        ]
        if len(button_list) > 0:
            print(button_list)

        dir = get_arm_direction(joysticks[0])
        if prev_dir is None or norm(dir - prev_dir) > 0.01 or norm(dir) > 0.01:
            print(prev_dir is None, norm(dir - prev_dir) > 0.01 if prev_dir is not None else False, norm(dir) > 0.01)
            # Try to apply this direction to the current position and set the target to that.
            angles = get_current_angles()
            pos = kinematics.get_pos(np.vectorize(radians)(angles))
            new_pos = pos + dir
            solution = kinematics.get_motor_settings(new_pos)
            print(pos, new_pos)
            new_angles = np.vectorize(degrees)(solution.x)
            print(angles, new_angles)
            set_target_angles(new_angles)
            prev_dir = dir


        # Limit to 30 frames per second.
        clock.tick(60)


if __name__ == "__main__":
    main()
    # If you forget this line, the program will 'hang'
    # on exit if running from IDLE.
    pygame.quit()
