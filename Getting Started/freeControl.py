#!/usr/bin/env python
#
 
import nxt
import sys
import tty
import termios
import nxt.locator
from nxt.sensor import *
from nxt.motor import *
import os
from pynput import keyboard

#nxt.locator.make_config()

sens = 360
sensTurn = 60
curSens = 5
power = 10

brick = nxt.locator.find_one_brick(debug=True)
left = nxt.Motor(brick, PORT_B)
right = nxt.Motor(brick, PORT_C)
both = nxt.SynchronizedMotors(left, right, 0)
camera = nxt.Motor(brick, PORT_A)
leftboth = nxt.SynchronizedMotors(left, right, 100)
rightboth = nxt.SynchronizedMotors(right, left, 100)
guideLight = nxt.Color20(brick, PORT_4)
#frontSense = nxt.Ultrasonic(brick, PORT_1)

blue = Type.COLORBLUE
green = Type.COLORGREEN
red = Type.COLORRED
off = Type.COLORNONE
curCol = off
guideLight.set_light_color(curCol)
curCol = green
camDeg = 0

camera.turn(power, sens, False)


def getchar():
    print('Press a command key:')
    with keyboard.Events() as events:
    # Block for as much as possible
        event = events.get(1.0)
        if isinstance(event, type(None)):
            ch = ' '
        else:
            ch = event.key
        return ch

ch = ' '
print("Ready")

while ch != keyboard.KeyCode.from_char('q'):
    ch = getchar()
    #print(ch)
    if ch == keyboard.KeyCode.from_char('w'):
        print("Forwards")
        both.turn(power, sens, False)
    elif ch == keyboard.KeyCode.from_char('s'):
        print("Backwards")
        both.turn(-power, sens, False)
        print('Backup Room:', frontSense.get_sample())
    elif ch == keyboard.KeyCode.from_char('a'):
        print("Left")
        leftboth.turn(100, sensTurn, False)
    elif ch == keyboard.KeyCode.from_char('d'):
        print("Right")
        rightboth.turn(100, sensTurn, False)
    elif ch == keyboard.KeyCode.from_char('b'):
        print('Space in front:', frontSense.get_sample())
    elif ch == keyboard.KeyCode.from_char('e'):
        if camDeg == 0:
            print("Camera cannot go lower")
        else:
            print("Camera Down:", camDeg)
            camera.turn(25, 20, True)
            camDeg = camDeg - 1
    elif ch == keyboard.KeyCode.from_char('r'):
        if camDeg == 3:
            print("Camera cannot go higher")
        else:
            print("Camera Up:", camDeg)
            camera.turn(-25, 20, True)
            camDeg = camDeg + 1

    elif ch == keyboard.KeyCode.from_char('z'):
        rightboth.turn(100, 3600, False)
        leftboth.turn(-100, 3600, False)
        print("Spin")
if camDeg == 3:
    camera.turn(25, 60, False)
elif camDeg == 2:
    camera.turn(25, 40, False)
elif camDeg == 1:
    camera.turn(25, 20, False)
guideLight.set_light_color(off)
brick.sock.close()
print("Finished")
