
import nxt
import nxt.usbsock
import sys
import nxt.locator
from nxt.sensor import *
from nxt.motor import *
import numpy as np
import argparse
import os


#nxt.locator.make_config()


class LoadBrick:
    def __init__(self):
        self.brick = nxt.locator.find_one_brick()
        self.camera = nxt.Motor(self.brick, PORT_A)
        self.drive = nxt.Motor(self.brick, PORT_B)
        self.steer = nxt.Motor(self.brick, PORT_C)
        self.enable_key = nxt.Touch(self.brick, PORT_1)
        self.frontSense = nxt.Ultrasonic(self.brick, PORT_2)
        self.steer_angle = 0

    def test(self):
        # Touch sensor latency test
        start = time.time()
        for i in range(4):
            self.enable_key.get_sample()
        stop = time.time()
        print('touch latency: %s ms' % (1000 * (stop - start) / 5.0))

        # Ultrasonic sensor latency test
        start = time.time()
        for i in range(4):
            self.frontSense.get_sample()
        stop = time.time()
        print('ultrasonic latency: %s ms' % (1000 * (stop - start) / 5.0))
        print("The brick was tested successfully.")

    def calibrate(self):
        print('Calibrating: Make sure that the steering wheel is straight.')
        self.drive.reset_position(relative=False)
        self.steer.reset_position(relative=False)
        print("The brick was calibrated successfully.")

    def play_note(self):
        C = 523
        D = 587
        E = 659
        G = 784
        R = None
        for note in [E, D, C, D, E, E, E, R,
                     D, D, D, R,
                     E, G, G, R, E, D, C, D, E, E, E, E, D, D, E, D, C]:
            if note:
                self.brick.play_tone_and_wait(note, 500)
            else:
                time.sleep(0.5)

    def motor_idle(self):
        self.drive.idle()
        self.steer.idle()
        self.camera.idle()

    def turn_off(self):
        # Turn off motors
        self.motor_idle()
        self.brick.sock.close()


def steer_command(brick_name, power, steer_val):
    if power <= 0:
        print('Warning(function steer_command): The power input must be positive.')
        power = abs(power)

    if motor_idle(brick_name.steer):
        brick_name.steer.turn(-np.sign(steer_val) * power, abs(int(abs(steer_val) - 3)), False) # The tuning parameter 30 is a sort of magic
        brick_name.steer_angle = brick_name.steer_angle + steer_val
        print('Steering angle = ', brick_name.steer_angle)
    else:
        print('Warning: Steering command is blocked because the motor is running!')
        return None


def zero_steering(brick_name, power):
    # Return the steering to its initial state
    if abs(brick_name.steer_angle) > 40:
        steer_command(brick_name, power, -brick_name.steer_angle)


def motor_idle(motor_name):
    if motor_name._read_state()[0].mode == 0:
        return 1
    else:
        return 0


def test_sin_cmd(t):
    freq = 0.5
    x_target = 0.4 * np.sin(freq * t)
    y_target = 0.4 * np.sin(freq * t)
    return x_target, y_target


def tracking(brick, x_target, y_target, args_control):
    if brick.frontSense.get_sample() < args_control.prox_front:
        print('STOP : The front sensor is blocked!!!')
        brick.drive.idle()
        time.sleep(0.5)
    else:
        if x_target == -1.0 and y_target == -1.0:    # No target
            print('No target is detected!!')
            brick.motor_idle()
        else:
            if motor_idle(brick.drive):
                brick.drive.run(args_control.power_dr)

            if -args_control.straight_threshold <= x_target <= args_control.straight_threshold:  # Target straight a head
                print('Move forward')
                # brick.drive.turn(power_dr, step_dr, brake=False)
                zero_steering(brick, args_control.power_st)

            elif brick.steer_angle > -args_control.max_steer_angle+args_control.step_st and x_target < -0.1: # Turn left
                print('Turn left')
                steer_command(brick, args_control.power_st, -args_control.step_st)

            elif brick.steer_angle < args_control.max_steer_angle-args_control.step_st and x_target > 0.1:  # Turn right
                print('Turn right')
                steer_command(brick, args_control.power_st, args_control.step_st)


def add_control_args(parser):
    # Tuning parameters:
    parser.add_argument('--control_dt', type=float, default=0.1,
                        help='Control implementation delta t')
    parser.add_argument('--straight_threshold', type=float, default=0.1,
                        help='Go forward for x: -straight_threshold < x < straight_threshold')
    parser.add_argument('--step_dr', type=int, default=300,
                        help='Rotation of drive motor per each command')
    parser.add_argument('--step_st', type=int, default=80,
                        help='Rotation of steering motor per each command')
    parser.add_argument('--step_cam', type=int, default=20,
                        help='Rotation of camera motor per each command')
    parser.add_argument('--power_dr', type=int, default=110,
                        help='Power of drive motor (-120 < power < 120)')
    parser.add_argument('--power_st', type=int, default=110,
                        help='Power of steering motor (-120 < power < 120)')
    parser.add_argument('--power_cam', type=int, default=20,
                        help='Power of camera motor (-120 < power < 120)')
    parser.add_argument('--max_steer_angle', type=int, default=200,
                        help='Maximum steering angle'),
    parser.add_argument('--prox_front', type=int, default=30,
                        help='Stops if the measurement of the ultrasonic front sensor is less than prox_front')


def main():
    parser_control = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    add_control_args(parser_control)
    args_control = parser_control.parse_args()
    brick = LoadBrick()
    # brick.play_note()
    brick.test()
    brick.calibrate()
    t0 = time.time()
    t_OLD = 0
    while brick.enable_key.get_sample():
        t = time.time() - t0
        if t-t_OLD >= args_control.control_dt:
            x_target = 0.05  # -1 <= x_target <=1
            y_target = 0.1  # -1 <= y_target <=1 (for no target: x_target == -1.0 and y_target == -1.0)
            (x_target, y_target) = test_sin_cmd(t)
            print("Target location ( t = ", t, ") : x = ", x_target, " , y = ", y_target)
            tracking(brick, x_target, y_target, args_control)
            t_OLD = t

        time.sleep(0.1)

    zero_steering(brick, args_control.power_st)
    time.sleep(1)
    brick.turn_off()
    print("Finished")


if __name__ == '__main__':
    main()
