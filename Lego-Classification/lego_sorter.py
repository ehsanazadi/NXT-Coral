from control import LoadBrick, add_control_args
from classify_server import main as classify_server_main
from classify import main as classify_main
import argparse


def main_arg_parser():
    parser_main = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser_main.add_argument('--model',
                             default='./models/output_tflite_graph_edgetpu.tflite',
                             help='.tflite model path')
    parser_main.add_argument('--labels', default='./models/labels.txt',
                             help='labels file path')
    parser_main.add_argument('--server_mode', default='True',
                             help='Run in server mode.')
    add_control_args(parser_main)
    args = parser_main.parse_args()
    return args


def main():
    args_main = main_arg_parser()
    brick = None
    #brick = LoadBrick()
    # brick.play_note()
    #brick.test()
    #brick.calibrate()

    args = (['--model', args_main.model,
             '--labels', args_main.labels,
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
        classify_server_main(args)
    else:
        classify_main(args)


if __name__ == '__main__':
    main()
