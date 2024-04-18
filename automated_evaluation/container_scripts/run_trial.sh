#!/bin/bash

cd /container_scripts

chmod +x run_trial.py
chmod +x run_trial_with_output.sh

source /opt/ros/iron/setup.bash
source /workspace/install/setup.bash

python3 run_trial.py $1 $2