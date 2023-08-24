from dataclasses import dataclass

from fltk import *
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

from math import *


@dataclass
class SimFixedPoint:
    """Unit: meter Direction: Up"""

    y: float

    """Unit: meter Direction: Right"""
    x: float

    # Sim is two dimensional, so there's no Z.


@dataclass
class SimEmptyEndpoint:
    """Represents an endpoint that is not attached to anything."""

    pass


@dataclass
class SimMotor:
    angle: float
    """Current angle in degrees. 0 means 'pointing to the right'. 90 is pointing up."""

    speed: float
    """Speed in degrees/sec."""


@dataclass
class SimBeam:
    length: float
    """Meters"""


@dataclass
class SimObject:
    """List of members.

    The first member will always be a fixed point and the remaining
    members will be beam, motor, beam, motor, etc."""

    members: list[SimFixedPoint | SimMotor | SimBeam]


def simulate_step(m: SimMotor, timestep: float):
    m.angle += m.speed * timestep


def simulate_step(o: SimObject, timestep: float):
    for obj in o.members:
        simulate_step(obj, timestep)


def simulate_step(o: any, timestep: float):
    pass


def sim_draw_beam(o: SimBeam):
    print("before draw")
    glColor3f(0.1, 0.1, 0.9)  # Mostly blue
    glBegin(GL_QUADS)
    glVertex2f(0, -0.05)
    glVertex2f(o.length, -0.05)
    glVertex2f(o.length, 0.05)
    glVertex2f(0, 0.05)
    print("before end")
    glEnd()
    print("before transate")
    glTranslatef(o.length, 0.0, 0.0)


def sim_draw_fixed(o: SimFixedPoint):
    print("color")
    glColor(0.9, 0.1, 0.1)  # Mostly red
    print("begin")
    glBegin(GL_TRIANGLE_FAN)
    print("vertex 1")
    glVertex2f(0.0, 0.0)
    for idx in range(101):
        print("vertex ", idx + 1)
        angle = idx * 2.0 * M_PI / 100
        glVertex2f(cos(angle) * 0.5, sin(angle) * 0.5)
    print("before end")
    glEnd()
    print("after end")


def sim_draw_motor(o: SimMotor):
    glColor3f(0.1, 0.9, 0.1)  # Mostly green
    glBegin(GL_QUADS)
    glVertex2f(0.5, 0.5)
    glVertex2f(0.5, -0.5)
    glVertex2f(-0.5, -0.5)
    glVertex2f(-0.5, 0.5)
    glEnd()
    glRotatef(o.angle, 0.0, 0.0, 1.0)
    pass


def sim_draw(o: SimObject):
    for child in o.members:
        print(child)
        match child:
            case SimMotor():
                sim_draw_motor(child)
            case SimBeam():
                sim_draw_beam(child)
            case SimFixedPoint():
                sim_draw_fixed(child)


have_initted_opengl = False


class My_GL_Window(Fl_Gl_Window):
    def __init__(self, obj: SimObject):
        Fl_Gl_Window.__init__(self, 100, 100, 1920, 1080, "my gl window")
        self._obj = obj

    def draw(self):
        if self.damage() == 0:
            return

        # glClearColor(0.0, 0.0, 0.0, 1.0)
        # glClear(GL_COLOR_BUFFER_BIT)

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluOrtho2D(-20, 20, -2, 20)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        sim_draw(self._obj)
        glFlush()


def create_and_show_window():
    global have_initted_opengl
    if not have_initted_opengl:
        have_initted_opengl = True

    wind = My_GL_Window(
        SimObject(
            [
                SimMotor(angle=90, speed=0),
                SimBeam(length=10),
                SimMotor(angle=150, speed=0),
                SimBeam(length=7),
                SimMotor(angle=-20, speed=0),
                SimBeam(length=3),
            ]
        )
    )
    wind.end()
    wind.show()
    Fl.run()


if __name__ == "__main__":
    create_and_show_window()
