# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""A demo which runs object detection on camera frames.

export TEST_DATA=/usr/lib/python3/dist-packages/edgetpu/test_data

Run face detection model:
python3 -m edgetpuvision.detect \
  --model ${TEST_DATA}/mobilenet_ssd_v2_face_quant_postprocess_edgetpu.tflite

Run coco model:
python3 -m edgetpuvision.detect \
  --model ${TEST_DATA}/mobilenet_ssd_v2_coco_quant_postprocess_edgetpu.tflite \
  --labels ${TEST_DATA}/coco_labels.txt
"""

import argparse
import colorsys
import itertools
import time
import math
import collections

from pycoral.adapters import detect
from pycoral.utils import edgetpu
from control import zero_steering, tracking
# import svgwrite
import svg
import utils
from apps import run_app

# from pose_engine import PoseEngine
from pose_engine import KeypointType

CSS_STYLES = str(svg.CssStyle({'.back': svg.Style(fill='black',
                                                  stroke='black',
                                                  stroke_width='0.5em'),
                               '.bbox': svg.Style(fill_opacity=0.0,
                                                  stroke_width='0.1em')}))

EDGES = (
    (KeypointType.NOSE, KeypointType.LEFT_EYE),
    (KeypointType.NOSE, KeypointType.RIGHT_EYE),
    (KeypointType.NOSE, KeypointType.LEFT_EAR),
    (KeypointType.NOSE, KeypointType.RIGHT_EAR),
    (KeypointType.LEFT_EAR, KeypointType.LEFT_EYE),
    (KeypointType.RIGHT_EAR, KeypointType.RIGHT_EYE),
    (KeypointType.LEFT_EYE, KeypointType.RIGHT_EYE),
    (KeypointType.LEFT_SHOULDER, KeypointType.RIGHT_SHOULDER),
    (KeypointType.LEFT_SHOULDER, KeypointType.LEFT_ELBOW),
    (KeypointType.LEFT_SHOULDER, KeypointType.LEFT_HIP),
    (KeypointType.RIGHT_SHOULDER, KeypointType.RIGHT_ELBOW),
    (KeypointType.RIGHT_SHOULDER, KeypointType.RIGHT_HIP),
    (KeypointType.LEFT_ELBOW, KeypointType.LEFT_WRIST),
    (KeypointType.RIGHT_ELBOW, KeypointType.RIGHT_WRIST),
    (KeypointType.LEFT_HIP, KeypointType.RIGHT_HIP),
    (KeypointType.LEFT_HIP, KeypointType.LEFT_KNEE),
    (KeypointType.RIGHT_HIP, KeypointType.RIGHT_KNEE),
    (KeypointType.LEFT_KNEE, KeypointType.LEFT_ANKLE),
    (KeypointType.RIGHT_KNEE, KeypointType.RIGHT_ANKLE),
)

Point = collections.namedtuple('Point', ['x', 'y'])
Point.distance = lambda a, b: math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)
Point.distance = staticmethod(Point.distance)

Keypoint = collections.namedtuple('Keypoint', ['point', 'score'])

Pose = collections.namedtuple('Pose', ['keypoints', 'score'])


def shadow_text(dwg, x, y, text, font_size=16):
    dwg.add(dwg.text(text, insert=(x + 1, y + 1), fill='black',
                     font_size=font_size, style='font-family:sans-serif'))
    dwg.add(dwg.text(text, insert=(x, y), fill='white',
                     font_size=font_size, style='font-family:sans-serif'))


def draw_pose(dwg, pose, src_size, inference_box, color='yellow', threshold=0.2):
    box_x, box_y, box_w, box_h = inference_box
    scale_x, scale_y = src_size[0] / box_w, src_size[1] / box_h
    xys = {}
    for label, keypoint in pose.keypoints.items():
        if keypoint.score < threshold: continue
        # Offset and scale to source coordinate space.
        kp_x = int((keypoint.point[0] - box_x) * scale_x)
        kp_y = int((keypoint.point[1] - box_y) * scale_y)

        xys[label] = (kp_x, kp_y)
        dwg.add(dwg.circle(center=(int(kp_x), int(kp_y)), r=5,
                           fill='cyan', fill_opacity=keypoint.score, stroke=color))

    for a, b in EDGES:
        if a not in xys or b not in xys: continue
        ax, ay = xys[a]
        bx, by = xys[b]
        dwg.add(dwg.line(start=(ax, ay), end=(bx, by), stroke=color, stroke_width=2))


def size_em(length):
    return '%sem' % str(0.6 * (length + 1))


def overlay(title, poses, inference_time, inference_rate, layout, src_size=(640, 480), color='yellow', threshold=0.2):
    x0, y0, width, height = layout.window
    font_size = 0.03 * height

    defs = svg.Defs()
    defs += CSS_STYLES

    doc = svg.Svg(width=width, height=height,
                  viewBox='%s %s %s %s' % layout.window,
                  font_size=font_size, font_family='monospace', font_weight=500)
    doc += defs

    for pose in poses:
        inference_width, inference_height = layout.inference_size
        bbox = pose.bbox.scale(1.0 / inference_width, 1.0 / inference_height).scale(*layout.size)
        box_x, box_y, box_w, box_h = bbox.xmin, bbox.ymin, bbox.width, bbox.height
        # box_x, box_y, box_w, box_h = inference_box
        scale_x, scale_y = src_size[0] / inference_width, src_size[1] / inference_height
        xys = {}
        for label, keypoint in pose.keypoints.items():
            if keypoint.score < threshold: continue
            # Offset and scale to source coordinate space.
            kp_x = int((keypoint.point[0] - box_x) * scale_x)
            kp_y = int((keypoint.point[1] - box_y) * scale_y)

            xys[label] = (kp_x, kp_y)
            doc += svg.Circle(cx=int(kp_x), cy=int(kp_y), r=5,
                              fill='cyan', fill_opacity=keypoint.score, stroke=color, _class='bbox')
    return str(doc)
'''
        for a, b in EDGES:
            if a not in xys or b not in xys: continue
            ax, ay = xys[a]
            bx, by = xys[b]
            dwg.add(dwg.line(start=(ax, ay), end=(bx, by), stroke=color, stroke_width=2))

    for pose in poses:
        inference_width, inference_height = layout.inference_size
        bbox = obj.bbox.scale(1.0 / inference_width, 1.0 / inference_height).scale(*layout.size)
        x, y, w, h = bbox.xmin, bbox.ymin, bbox.width, bbox.height
        if labels.get(obj.id, obj.id) == target_label:
            for count in range(5):
                doc += svg.Circle(cx=x + w / 2, cy=y + h / 2, r=0.25 * math.sqrt(w ** 2 + h ** 2) + count,
                                  style='stroke:%s' % color, _class='bbox')

            doc += svg.Rect(x=x + w / 2, y=y + h,
                            width=size_em(len(caption)), height='1.2em', fill=color)
            t = svg.Text(x=x + w / 2, y=y + h, fill='black')
            if obj.score > target_score:
                target_x = x + w / 2
                target_y = y + h / 2
                target_score = obj.score
        else:
            doc += svg.Rect(x=x, y=y, width=w, height=h,
                            style='stroke:%s' % color, _class='bbox')
            doc += svg.Rect(x=x, y=y + h,
                            width=size_em(len(caption)), height='1.2em', fill=color)
            t = svg.Text(x=x, y=y + h, fill='black')

        t += svg.TSpan(caption, dy='1em')
        doc += t

    ox = x0 + 20
    oy1, oy2 = y0 + 20 + font_size, y0 + height - 20

    # Title
    if title:
        titles = ['Project NXT-Coral _ object detection with pre-trained model:', title]
        for i, title_i in enumerate(titles):
            y = oy1 + i * 1.7 * font_size
            doc += svg.Rect(x=0, y=0, width=size_em(len(title_i)), height='1em',
                            transform='translate(%s, %s) scale(1,-1)' % (ox, y), _class='back')
            doc += svg.Text(title_i, x=ox, y=y, fill='white')

    # Info
    if target_score > 0:
        lines = [
            'Detected objects: %d' % len(objs),
            'Target %s is detected at x=%d and y=%d' % (target_label, target_x, target_y),
            'Inference time: %.2f ms (%.2f fps)' % (inference_time * 1000, 1.0 / inference_time)
        ]
    else:
        lines = ['Detected objects: %d' % len(objs),
                 'Target %s is not detected!' % str(target_label),
                 'Inference time: %.2f ms (%.2f fps)' % (inference_time * 1000, 1.0 / inference_time)]

    for i, line in enumerate(reversed(lines)):
        y = oy2 - i * 1.7 * font_size
        doc += svg.Rect(x=0, y=0, width=size_em(len(line)), height='1em',
                        transform='translate(%s, %s) scale(1,-1)' % (ox, y), _class='back')
        doc += svg.Text(line, x=ox, y=y, fill='white')
'''



def ParseOutput(interpreter, args):
    """Parses interpreter output tensors and returns decoded poses."""
    _, input_height, input_width, input_depth = interpreter.get_input_tensor_shape()
    keypoints = interpreter.get_output_tensor(0)
    keypoint_scores = interpreter.get_output_tensor(1)
    pose_scores = interpreter.get_output_tensor(2)
    num_poses = interpreter.get_output_tensor(3)
    poses = []
    for i in range(int(num_poses)):
        pose_score = pose_scores[i]
        pose_keypoints = {}
        for j, point in enumerate(keypoints[i]):
            y, x = point
            if args.mirror:
                y = input_width - y
            pose_keypoints[KeypointType(j)] = Keypoint(
                Point(x, y), keypoint_scores[i, j])
        poses.append(Pose(pose_keypoints, pose_score))
    return poses


def render_gen(args, brick):
    fps_counter = utils.avg_fps_counter(30)

    interpreters, titles = utils.make_interpreters(args.model)
    assert utils.same_input_image_sizes(interpreters)
    interpreters = itertools.cycle(interpreters)
    interpreter = next(interpreters)

    draw_overlay = True

    width, height = utils.input_image_size(interpreter)
    yield width, height

    output = None
    t0 = time.time()  # MY
    t_OLD = 0  # My
    brick_en = True  # My

    while True:
        tensor, layout, command = (yield output)

        inference_rate = next(fps_counter)
        if draw_overlay:
            start = time.monotonic()
            edgetpu.run_inference(interpreter, tensor)
            inference_time = time.monotonic() - start

            poses = ParseOutput(interpreter, args)

            title = titles[interpreter]
            output = overlay(title, poses, inference_time, inference_rate, layout)
        else:
            output = None

        if command == 'o':
            draw_overlay = not draw_overlay
        elif command == 'n':
            interpreter = next(interpreters)


'''        ##MY##
        target_label = args.target_label
        target_threshold = args.target_threshold
        if brick_en:
            if brick.enable_key.get_sample():
                t = time.time() - t0
                if t - t_OLD >= args.control_dt:
                    target_x = -1
                    target_y = -1
                    target_score = 0
                    for obj in objs:
                        if labels.get(obj.id, obj.id) == target_label:
                            # Finding the target with the largest score
                            if obj.score > target_threshold and obj.score > target_score:
                                inference_width, inference_height = layout.inference_size
                                bbox = obj.bbox.scale(1.0 / inference_width, 1.0 / inference_height).scale(*layout.size)
                                x, y, w, h = bbox.xmin, bbox.ymin, bbox.width, bbox.height
                                target_x = (x + w / 2) / width - 1
                                target_y = ((y + h / 2) / height - 1) * -2
                                target_score = obj.score
                    if target_score > 0:
                        print('{} with score {} % at X={}, Y={}'.format(target_label, target_score * 100, target_x,
                                                                        target_y))
                    tracking(brick, target_x, target_y, args)
                    t_OLD = t
            else:
                zero_steering(brick, args.power_st)
                time.sleep(1)
                brick.turn_off()
                brick_en = False
                print('The link with NXT brick is deactivated.')

        ##MY##
'''


def add_render_gen_args(parser):
    parser.add_argument('--model',
                        help='.tflite model path')
    parser.add_argument('--labels',
                        help='labels file path')
    parser.add_argument('--target_label', default=None,
                        help='The label of the target object to follow')
    parser.add_argument('--target_threshold', type=float, default=None,
                        help='Threshold of the target object')
    parser.add_argument('--top_k', type=int, default=50,
                        help='Max number of objects to detect')
    parser.add_argument('--threshold', type=float, default=0.1,
                        help='Detection threshold')
    parser.add_argument('--min_area', type=float, default=0.0,
                        help='Min bounding box area')
    parser.add_argument('--max_area', type=float, default=1.0,
                        help='Max bounding box area')
    parser.add_argument('--filter', default=None,
                        help='Comma-separated list of allowed labels')
    parser.add_argument('--color', default=None,
                        help='Bounding box display color'),
    parser.add_argument('--print', default=False, action='store_true',
                        help='Print inference results')


def main(raw_args=None):
    run_app(add_render_gen_args, render_gen, raw_args)


if __name__ == '__main__':
    main()
