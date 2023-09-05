#! /usr/bin/env python3

import unittest
from kinematics import get_pos, get_err, get_motor_settings
from math import sin, cos, radians
import numpy.testing as npt


class TestGetPos(unittest.TestCase):
    def test_45(self):
        # Note: X is two greater than Y because X is shifted by two due to the offset
        # from the turntable base.
        npt.assert_allclose(get_pos((0, radians(45), 0)),
                            (2 + (35 * sin(radians(45))), (35 * sin(radians(45))), 0))

    def test_45_rot_45(self):
        # Note: X is two greater than Y because X is shifted by two due to the offset
        # from the turntable base.
        r = get_pos((0, radians(45), 0))[0]

        # Rotating by 45 degrees will make r the hypotenuse of a right triangle with two
        # equal sides. Y remains unchanged due to the height being unaffected by rotation.
        x_and_z = r * sin(radians(45))

        npt.assert_allclose(get_pos((radians(45), radians(45), 0)),
                            (x_and_z, (35 * sin(radians(45))), x_and_z))

    def test_get_err(self):
        input = (radians(45), radians(45), 0)
        actual = get_pos(input)
        self.assertAlmostEqual(get_err(input, actual), 0)

    def test_get_err_with_introduced_error(self):
        input = (radians(45), radians(45), 0)
        actual = get_pos(input)
        actual[0] += 3
        actual[2] += 4
        self.assertAlmostEqual(get_err(input, actual), 5)

    def test_minimize(self):
        # Running a known good motor setting's position output should give us the same input
        # motor settings when the output is sent through inverse kinematics.
        input = (radians(45), radians(45), 0)
        output_pos = get_pos(input)
        # As long as we're within 1% of correct, we're good. There's far more slop than that
        # in the motors and gearing.
        npt.assert_allclose(get_motor_settings(output_pos).x, input, rtol=1, atol=radians(1))



if __name__ == '__main__':
    unittest.main()
