from control import LoadBrick, add_control_args
from pose_detect_server import main as detect_server_main
from pose_detect import main as detect_main
import argparse


def main_arg_parser():
    parser_main = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser_main.add_argument('--model',
                             default='./models/mobilenet/posenet_mobilenet_v1_075_481_641_quant_decoder_edgetpu.tflite',
                             help='.tflite model path')
    parser_main.add_argument('--target_threshold', type=float, default=0.15,
                             help='Threshold of the target object')
    parser_main.add_argument('--server_mode', default='True',
                             help='Run in server mode.')
    add_control_args(parser_main)
    args = parser_main.parse_args()
    return args


def main():
    args_main = main_arg_parser()
    # brick = LoadBrick()
    brick = None
    # brick.play_note()
    # brick.test()
    # brick.calibrate()

    args = (['--model', args_main.model,
             '--control_dt', str(args_main.control_dt),
             '--straight_threshold', str(args_main.straight_threshold),
             '--step_dr', str(args_main.step_dr),
             '--step_st', str(args_main.step_st),
             '--step_cam', str(args_main.step_cam),
             '--power_dr', str(args_main.power_dr),
             '--power_st', str(args_main.power_st),
             '--power_cam', str(args_main.power_cam),
             '--max_steer_angle', str(args_main.max_steer_angle),
             '--prox_front', str(args_main.prox_front)],
            brick)
    if args_main.server_mode.lower() in ['true', 't']:
        detect_server_main(args)
    else:
        detect_main(args)


if __name__ == '__main__':
    main()
