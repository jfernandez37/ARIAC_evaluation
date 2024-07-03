import os
import yaml
import subprocess
import numpy as np
from time import time, sleep
import cv2
import docker
import pyautogui

from score_trial import score_trial
from docker.models.containers import Container as DockerContainer
from pathlib import Path
from typing import Optional

def get_competing_teams() -> list[str]:
    automated_eval_folder = os.path.abspath(os.path.join(__file__, "..", ".."))

    competitor_configs: list[str] = []
    for root, _, files in os.walk(os.path.join(automated_eval_folder, "competitor_configs")):
        for file in files:
            if not file.endswith('.yaml'):
                continue

            # if "nist_competitor" in file:
            #     continue

            competitor_configs.append(os.path.join(root, file))

    team_names = []
    for path in competitor_configs:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                trial_config = yaml.safe_load(f)
        except (IOError, yaml.YAMLError):
            print(f'Unable to parse trial config: {path}')

        team_names.append(trial_config['team_name'])

    return team_names


def get_trial_names() -> list[str]:
    """Parses the logs folder of each team found to find all the trials which have been run.

    Returns:
        list[str]: list of trial names
    """
    automated_eval_folder = os.path.abspath(os.path.join(__file__, "..", ".."))

    trial_names = []

    for _, _, files in os.walk(os.path.join(automated_eval_folder, "trials")):
        for file in files:
            if file.endswith('.yaml'):
                trial_names.append(file.replace(".yaml", ""))

    return trial_names


def generate_summary(final_scores: dict[str, float]):
    print("Final Scores:")
    for team, score in final_scores.items():
        print(f"\t{team}: {score}")


def filter_best_trial_logs(team_names, trial_names):
    commands = []
    if not os.path.exists("filtered_state_logs"):
        os.mkdir("filtered_state_logs")
    for team in team_names:
        if not os.path.exists(os.path.join("filtered_state_logs", team)):
            os.mkdir(os.path.join("filtered_state_logs", team))
        for trial in trial_names:
            if not os.path.exists(os.path.join("filtered_state_logs", team, trial)):
                os.mkdir(os.path.join("filtered_state_logs", team, trial))
    for trial in trial_names:
        trial_info = score_trial(trial, team_names)
        for team in team_names:
            if trial_info.team_best_file_logs[team] != None:
                commands.append(["./filter_state_log.sh", os.path.join(f"{trial_info.team_best_file_logs[team]}","state.log"), os.path.join(os.getcwd(),"filtered_state_logs", team, trial,"state.log")])
    subprocesses = [subprocess.Popen(command) for command in commands] # Runs each of the filtering commands in parallel
    print("Filtering state.log" + ("" if len(commands)<=1 else "s") + "...")
    end_codes = [s.wait() for s in subprocesses] # Waits until all of the best state logs are filtered
    print(f"Saved state logs" + ("" if len(commands)<=1 else "s")+"\n\nTo find filtered state.logs, go to /filtered_state_logs/team/trial")

def record_each_trial_log(team_names, trial_names):
    # recorder = pyscreenrec.ScreenRecorder()
    docker_client = docker.DockerClient()
    all_containers: list[DockerContainer] = docker_client.containers.list(all=True)
        
    team_containers: dict[str, Optional[DockerContainer]] = {}
    for team in team_names:
        for container in all_containers:
            if container.name == team:
                team_containers[team] = container
                break
    
    for container in team_containers.values():
        print("Stopping container",container.name)
        container.stop()
        
    for trial in trial_names:
        for team in team_containers.keys():
            path = Path(os.path.join("recordings", team, trial))
            path.mkdir(parents=True, exist_ok=True)
    
    for trial in trial_names:
        for team, container in team_containers.items():
            if os.path.exists(os.path.join("filtered_state_logs", team, trial)):
                container.restart()
                
                # Specify resolution
                resolution = (1920, 1080)
                
                # Specify video codec
                codec = cv2.VideoWriter_fourcc(*"XVID")
                
                # Specify name of Output file
                filename = f"{team}_{trial}.avi"
                
                # Specify frames rate
                fps = 60.0
                
                # Creating a VideoWriter object
                out = cv2.VideoWriter(filename, codec, fps, resolution)

                keep_recording = True
                first = True
                
                subprocess.Popen(["./scoring_playback.sh", team, trial])
                
                start_time = time()
                while keep_recording:
                    # Take screenshot using PyAutoGUI
                    img = pyautogui.screenshot()
                
                    # Convert the screenshot to a numpy array
                    frame = np.array(img)
                    
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    
                    pause_frame = frame[960:1010, 530:580]
                    
                    if time() - start_time >= 25:
                        if not first:
                            comparison = prev == pause_frame
                            
                            keep_recording = comparison.all()
                        else:
                            print("first")
                            first = False
                        prev = pause_frame
                    
                    out.write(frame)
                    
                container.stop()
                print(f"Finished recording for {team} on trial {trial}")
                os.system(f"mv {team}_{trial}.avi {os.path.join('recordings', team, trial, f'{team}_{trial}.avi')}")
    for container in team_containers.values():
        print("Stopping container",container.name)
        container.stop()
    print("Done recording trials")

def main():
    # Get list of team names from competitor_configs directory (exclude nist_competitor)
    competing_teams = get_competing_teams()
    print(competing_teams)
    # Get name of all trials from trials directory
    trial_names = get_trial_names()

    final_scores: dict[str, float] = {team: 0.0 for team in competing_teams}

    # For all trials
    for trial in sorted(trial_names):

        # Get trial results
        results = score_trial(trial, competing_teams)

        # Add score for each team to final scores
        for team, score in results.trial_scores.items():
            if not team in final_scores.keys():
                continue

            final_scores[team] += score

        # Generate graphs

    # Sort final scores in descending order
    final_scores = dict(sorted(final_scores.items(), key=lambda item: -item[1]))

    # Generate summary
    generate_summary(final_scores)
    
    # Filter the state.logs
    filter_best_trial_logs(competing_teams, trial_names)
    
    # Screen records each trial
    record_each_trial_log(competing_teams, trial_names)


if __name__ == "__main__":
    main()