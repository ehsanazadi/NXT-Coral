I used the NXT 2.0 brick with the following parts (All of the following parts can be found on the Lego website):
NXT Package - 8547
Ultrasonic Sensor - 9846
3x Servo - 9842

I used the nxt-python (http://code.google.com/p/nxt-python/) package in conjuncture with my Coral Dev Board.

For the Coral Dev hardware I used a Coral Camera.

Below are the ports used for the sensors:
Drive Servo - Port B
Steering Servo - Port C
Camera Servo - Port A
Ultrasonic Sensor - Port 1

To run:
python3 selfdriving.py

for more detailed input arguments:
python3 selfdriving.py --model /.../mobilenet_ssd_v2_coco_quant_postprocess_edgetpu.tflite /
    --labels /.../coco_labels.txt /
    --target_label banana /
    --target_threshold 0.15 /
    --server_mode False

If you are running in the server mode open a browser in the client and go to the address:
http://192.168.100.2:4664/