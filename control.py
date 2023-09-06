#! /usr/bin/env python3

import client
import kinematics
import enum
import numpy as np
import numpy.typing as npt
from numpy.linalg import norm
from math import degrees, radians
import time
import pygame
from typing import Annotated, Any, Literal, Sequence, cast


def input_gain(x: float):
    return 0.4 * x + 0.6 * x**3


Vec3 = npt.NDArray[np.number[Any]]

# joystick 0: negative=-x positive=+x
# joystick 1: negative=-z positive=+z
# joystick 3: negative=+y positive=-y
# button 0: save pos
# button 2: replay positions
# button 3: clear positions


def get_x(j: pygame.joystick.JoystickType):
    return input_gain(j.get_axis(0))


def get_y(j: pygame.joystick.JoystickType):
    return input_gain(-j.get_axis(3))


def get_z(j: pygame.joystick.JoystickType):
    return input_gain(j.get_axis(1))


def get_arm_direction(j: pygame.joystick.JoystickType) -> Vec3:
    return np.array((get_x(j), get_y(j), get_z(j)))


_RANGES = client.ranges()

_turntable_true_throw = 180
_turntable_scale = (_RANGES[1] - _RANGES[0]) / _turntable_true_throw
_arm1_true_throw = 73
_arm1_scale = (_RANGES[3] - _RANGES[2]) / _arm1_true_throw
_arm2_true_throw = 167
_arm2_scale = (_RANGES[5] - _RANGES[4]) / _arm2_true_throw


def turntable_raw_to_logical(angle: float) -> float:
    # 90 is the reference point for the turntable, so we scale the difference between 90 and the computed
    # minimum.
    diff = 90 - angle
    return 90 - diff / _turntable_scale


def turntable_logical_to_raw(angle: float) -> float:
    diff = 90 - angle
    return 90 - diff * _turntable_scale


def arm1_raw_to_logical(angle: float) -> float:
    # 17 is the reference point for arm1, and it is also the minimum
    diff = angle - 17
    return 17 + diff / _arm1_scale


def arm1_logical_to_raw(angle: float) -> float:
    # 17 is the reference point for arm1, and it is also the minimum
    diff = angle - 17
    return 17 + diff * _arm1_scale


def arm2_raw_to_logical(angle: float) -> float:
    # -6 is the reference point for arm2, and it is also the minimum.
    diff = angle - (-6)
    return (-6) + diff / _arm2_scale


def arm2_logical_to_raw(angle: float) -> float:
    # 17 is the reference point for arm2, and it is also the minimum
    diff = angle - (-6)
    return -6 + diff * _arm2_scale


def get_current_angles() -> Vec3:
    (r1, r2, r3) = client.current_position()
    return np.array(
        (
            turntable_raw_to_logical(r1),
            arm1_raw_to_logical(r2),
            arm2_raw_to_logical(r3),
        )
    )


def set_target_angles(v: np.ndarray, in_ms: int = 500):
    r1, r2, r3 = v[0], v[1], v[2]
    client.set_target(
        in_ms,
        int(turntable_logical_to_raw(r1)),
        int(arm1_logical_to_raw(r2)),
        int(arm2_logical_to_raw(r3)),
    )


# get_current_xyz and set_target_xyz are the two locations where we convert from degrees to radians.
# (The kinematics module thinks in radians and the rest of the program in degrees.)


def get_current_xyz() -> Vec3:
    return kinematics.get_pos(np.vectorize(radians)(get_current_angles()))


def set_target_xyz(target_xyz: Vec3, in_ms: int = 500):
    sol = kinematics.get_motor_settings(target_xyz, initial_guess=get_current_angles())
    sol.x = np.vectorize(degrees)(sol.x)
    set_target_angles(sol.x, in_ms)
    return sol


class ControlMode(enum.Enum):
    REL = 0
    """Control a vector from the current position."""

    VIRTUAL_POINT = 1
    """Control a virtual point. The arm seeks that point."""

    AXES = 2
    """Control the axes directly."""


class ControlModel:
    def __init__(self, c: ControlMode):
        self._control_mode = c
        if c == ControlMode.VIRTUAL_POINT:
            self._point = get_current_xyz()
            self._last_update = time.time()
        self._prev_dir = None

    def handle_button_press(self, buttons: Sequence[int]):
        if len(buttons) > 0:
            print(buttons)

    def handle_stick_input(self, v: Vec3):
        try:
            match self._control_mode:
                case ControlMode.REL:
                    return self._handle_stick_rel(v)

                case ControlMode.VIRTUAL_POINT:
                    return self._handle_stick_virt_point(v)

                case ControlMode.AXES:
                    return self._handle_stick_axes(v)
        finally:
            self._prev_dir = v

    @staticmethod
    def _normalize_then_scale(v: Vec3, scale: float) -> Vec3:
        mag = float(norm(v))
        if mag > 1:
            scale /= mag
        return v * scale

    def _handle_stick_rel(self, v: Vec3):
        _MOVEMENT_SCALE = 2.0  # Max movement /s
        if self._prev_dir is None or norm(v) > 0.01 or norm(self._prev_dir) > 0.01:
            print('----------')
            print(v)
            # Try to apply this direction to the current position and set the target to that.
            pos = get_current_xyz()
            print(pos)
            scaled_dir = ControlModel._normalize_then_scale(v, _MOVEMENT_SCALE)
            print(scaled_dir)
            new_pos = pos + scaled_dir
            print(new_pos)
            set_target_xyz(new_pos)
            print('----------')

    def _handle_stick_virt_point(self, v: Vec3) -> None:
        new_time = time.time()
        if new_time - self._last_update < 0.001:
            return
        delta = new_time - self._last_update
        self._last_update = new_time

        MAX_MOVEMENT = 5
        movement_this_step = MAX_MOVEMENT * delta
        scaled_v = ControlModel._normalize_then_scale(v, movement_this_step)

        new_pos = self._point + scaled_v
        solver_result = set_target_xyz(new_pos)
        err = solver_result.fun
        if err < 1:
            # We only update the virtual point if the target point is in or near the
            # feasible region.
            self._point = new_pos


    def _handle_stick_axes(self, v: Vec3) -> None:
        pass


print("pygame init")
pygame.init()
print("pygame init done")


def main():
    # Used to manage how fast the screen updates.
    clock = pygame.time.Clock()

    controller = ControlModel(ControlMode.VIRTUAL_POINT)

    while True:
        if pygame.joystick.get_count() == 0:
            # Don't do anything unless there is a joystick
            clock.tick(1)
            print("no joy")
            continue


        joysticks = [pygame.joystick.Joystick(j) for j in range(pygame.joystick.get_count())]

        controller.handle_stick_input(get_arm_direction(joysticks[0]))

        buttons = [
            cast(int, event.button)
            for event in pygame.event.get()
            if event.type == pygame.JOYBUTTONDOWN
        ]
        controller.handle_button_press(buttons)

        # Limit to 30 frames per second.
        clock.tick(60)


if __name__ == "__main__":
    main()
    # If you forget this line, the program will 'hang'
    # on exit if running from IDLE.
    pygame.quit()
