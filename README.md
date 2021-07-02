# NXT-Coral
This repository contains the source files of a set of projects for running advanced real-time Machine Learning (ML) algorithms on Mindstorm NXT2 Lego brick with the assistance of a Google Coral Dev Board. 

## System Architecture:
Since the computational resource of the NXT brick is very limmited, the Coral board is used to perform real-time ML computations mostly using TensorFlow lite. The output of the Coral board is sent to the NXT brick using a live communication link (USB or Bluetooth)

## Required Hardware:
1- Coral Dev Board. (+ required cables + required power source)

2- NXT. (+ required cables + required motor/sensor lego parts)

## Software Platform:
1- Python

2- nxt-Pi

3- Tensorflow (/lite)

4- 

## Sub projects:

### Getting Started:
This project is used to check the communication link between the Coral board and the NXT block. In this project, a motor forward/backward command is sent to the NXT brick by the Coral board.

### Self-driving Lego Vehicle:
