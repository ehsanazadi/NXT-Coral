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

step_dr = 300
step_st = 100
step_cam = 20


power_dr = 90
power_st = 100
power_cam = 20
camDeg = 0


brick = nxt.locator.find_one_brick(debug=True)
camera = nxt.Motor(brick, PORT_A)
drive = nxt.Motor(brick, PORT_B)
steer = nxt.Motor(brick, PORT_C)

#frontSense = nxt.Ultrasonic(brick, PORT_1)




def getchar():
    print('Press a command key:')
    with keyboard.Events() as events:
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
    if ch == keyboard.KeyCode.from_char('w'):
        print("Forwards")
        drive.turn(power_dr, step_dr, brake=False)
    elif ch == keyboard.KeyCode.from_char('s'):
        print("Backwards")
        drive.turn(-power_dr, step_dr, brake=False)
        #print('Backup Room:', frontSense.get_sample())
    elif ch == keyboard.KeyCode.from_char('a'):
        print("Left")
        steer.turn(power_st, step_st, False)
    elif ch == keyboard.KeyCode.from_char('d'):
        print("Right")
        steer.turn(-power_st, step_st, False)
    elif ch == keyboard.KeyCode.from_char('b'):
        print('Space in front:', frontSense.get_sample())
'''    elif ch == keyboard.KeyCode.from_char('e'):
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
'''
'''
if camDeg == 3:
    camera.turn(25, 60, False)
elif camDeg == 2:
    camera.turn(25, 40, False)
elif camDeg == 1:
    camera.turn(25, 20, False)
'''
brick.sock.close()
print("Finished")
