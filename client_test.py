#!/usr/bin/env python3

"""A test for the client.

Set the target to then 75% of the range, then 25% of the range, then 50% of the range, for each arm.
Note that this can only be run after the server on the arm is listening for connections, because
this software is written super janky and we're just trying to live a little here."""

import client
import time

ranges = client.ranges()

turntable_throw = ranges[1] - ranges[0]
arm1_throw = ranges[3] - ranges[2]
arm2_throw = ranges[5] - ranges[4]

client.set_target(2000, ranges[0] + turntable_throw * .75, ranges[2] + arm1_throw * .75, ranges[4] + arm2_throw * .75)
time.sleep(5)
client.set_target(2000, ranges[0] + turntable_throw * .25, ranges[2] + arm1_throw * .25, ranges[4] + arm2_throw * .25)
time.sleep(5)
client.set_target(2000, ranges[0] + turntable_throw * .5, ranges[2] + arm1_throw * .5, ranges[4] + arm2_throw * .5)
time.sleep(5)
