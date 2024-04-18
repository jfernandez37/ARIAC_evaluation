#!/bin/bash

if [[ ! $1 ]] ; then
    echo "Team name argument not passed" 
    exit 1
fi

teamName=$1

# Run build script
docker exec $teamName rm -rf src/ARIAC/ariac_gazebo/config/trials/

docker exec $teamName rm -rf install/ariac_gazebo/share/ariac_gazebo/config

docker cp ./trials/ $teamName:/workspace/src/ARIAC/ariac_gazebo/config/

cmd="source /opt/ros/iron/setup.bash && source /workspace/install/setup.bash && colcon build --packages-select ariac_gazebo"

docker exec $teamName bash -c "$cmd"
