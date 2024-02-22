#!/bin/bash

# Example Pre-build script for NIST Competitor
echo "==== Installing apt dependencies"
apt-get update
apt-get install -y python3-pykdl
echo "==== Installing pip"
apt-get install -y python3-pip
echo "==== Installing pip dependencies"
pip install numpy
pip install pyassimp
pip install moveit
echo "==== Installing moveit"
apt-get install -y ros-iron-moveit*