#!/bin/bash

teamName=$1
trial=$2 

docker cp $PWD/filtered_state_logs/$teamName/$trial/state.log $teamName:/home

docker exec -it $teamName bash -c ". /container_scripts/unpaused_playback.sh"