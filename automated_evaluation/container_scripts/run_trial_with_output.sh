#!/bin/bash

ros2 launch $1 $2 $3 --noninteractive 2>&1 | tee test.txt