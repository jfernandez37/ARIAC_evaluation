from score_trial import (
    score_trial, 
    get_team_names,
    get_order_information
)
import os
import matplotlib.pyplot as plt
import numpy as np
import subprocess
import pyscreenrec
from time import sleep, time
import pyautogui
import cv2
import docker
from docker.models.containers import Container as DockerContainer
from typing import Optional
from pathlib import Path
from multiprocessing import Process
import multiprocessing as mp

mutex = []

def get_trial_names(team_names: list[str]) -> list[str]:
    """Parses the logs folder of each team found to find all the trials which have been run.

    Returns:
        list[str]: list of trial names
    """
    trial_names = []
    for team in team_names:
        automated_eval_folder = os.path.abspath(os.path.join(__file__, "..", ".."))
        for file in os.scandir(os.path.join(automated_eval_folder,"logs",team)):
            if file.is_dir():
                trial_names.append("_".join(os.path.basename(file).split("_")[:-1]))
    return sorted(list(set(trial_names)))

def get_total_scores(team_names: list[str],trial_names: list[str]) -> dict[str,float]:
    """Scores all of the trials and finds the final scores for each team

    Returns:
        dict[str,float]: dictionary where the keys are the team names and the values are their scores
    """
    final_scores_by_team = {team : 0 for team in team_names}
    for trial in trial_names:
        trial_info = score_trial(trial)
        for team in team_names:
            final_scores_by_team[team] += trial_info.trial_scores[team]
    return {k: v for k, v in sorted(final_scores_by_team.items(), key=lambda item: -item[1])}

def get_trial_scores_by_team(team_names: list[str],trial_names: list[str]) -> dict[str,list[float]]:
    """Gets the individual trial scores for each team and saves them into a list inside of a dictionary

    Returns:
        dict[str,float]: dictionary where the keys are the team names and the values are lists of the teams trial scores
    """
    all_trial_scores = {team: [] for team in team_names}
    for trial in trial_names:
        trial_info = score_trial(trial)
        for team in team_names:
            all_trial_scores[team].append(trial_info.trial_scores[team])
    return all_trial_scores

def total_raw_scores_by_team(team_names, trial_names):
    total_raw_scores = {team: 0 for team in team_names}
    for trial in trial_names:
        trial_info = score_trial(trial)
        for team in team_names:
            order_ids = [order.order_id for order in get_order_information(trial)]
            for order_id in order_ids:
                try:
                    total_raw_scores[team] += trial_info.team_submissions[team].order_submissions[order_id].raw_score
                except:
                    pass
    return total_raw_scores

def get_max_scores_for_trial(team_names, trial):
    order_ids = [order.order_id for order in get_order_information(trial)]
    trial_max_scores = {}
    for team_name in team_names:
        automated_eval_folder = os.path.abspath(os.path.join(__file__, "..", ".."))
        trial_log = os.path.join(automated_eval_folder,"logs",team_name,f"{trial}_1","trial_log.txt")
        if os.path.exists(trial_log):
            break
    try:
        with open(trial_log, "r") as file:
            lines = file.readlines()
    except IOError:
        print(f'Unable to open file: {trial_log}')
        return None

    # Get only order summary section of trial log
    start = [("Order Summary" in line) for line in lines].index(True) + 2
    end = [("Order Details" in line) for line in lines].index(True) - 2
    summary = lines[start:end]
    
    # Calculate the combined raw score for all orders
    for i in range(len(summary)//8):
        trial_max_scores[order_ids[i]] =  int(summary[(i * 8) + 4].split(":")[-1]) 
        
    return trial_max_scores

def addlabels(x,y):
    for i in range(len(x)):
        plt.text(i, y[i], y[i], ha = 'center')
        

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
        trial_info = score_trial(trial)
        for team in team_names:
            commands.append(["./filter_state_log.sh", os.path.join(f"{trial_info.team_best_file_logs[team]}","state.log"), os.path.join(os.getcwd(),"filtered_state_logs", team, trial,"state.log")])
    subprocesses = [subprocess.Popen(command) for command in commands] # Runs each of the filtering commands in parallel
    print("Filtering state.log" + ("" if len(commands)<=1 else "s") + "...")
    end_codes = [s.wait() for s in subprocesses] # Waits until all of the best state logs are filtered
    print(f"Saved state logs" + ("" if len(commands)<=1 else "s")+"\n\nTo find filtered state.logs, go to /filtered_state_logs/team/trial")

def screen_record(team, trial, recorder, l):
    print("In recorder process")
    recorder.start_recording(f"{team}_{trial}.mp4", 20)
    subprocess.Popen(["./scoring_playback.sh", team, trial])
    sleep(5)
    print("Waiting in recorder process")
    l.acquire()
    try:
        print("Out of wait in recorder process")
        recorder.stop_recording()
    finally:
        l.release()

def detect_pause_change(l, sleep_time):
    print("In pause scan thread")
    l.acquire()
    print("before sleep")
    sleep(sleep_time)
    print("after sleep")
    first = True
    keep_recording = True
    while keep_recording:
        # Take screenshot using PyAutoGUI
        img = pyautogui.screenshot()
    
        # Convert the screenshot to a numpy array
        frame = np.array(img)[960:1010, 530:580]
        
        
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        if not first:
            comparison = prev == frame
            
            if comparison.all():
                keep_recording = False
        else:
            print("first")
            first = False
        prev = frame
        cv2.imshow('Live', frame)
                    
        if cv2.waitKey(1) == ord('q'):
            break
        sleep(10)
    print("Change detected")
    l.release()
        
        

def record_each_trial_log(team_names, trial_names):
    # recorder = pyscreenrec.ScreenRecorder()
    docker_client = docker.DockerClient()
    all_containers: list[DockerContainer] = docker_client.containers.list(all=True)
    
    lock = mp.Lock()
    
    team_containers: dict[str, Optional[DockerContainer]]  = {team : None for team in team_names}
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
                
                # Specify frames rate. We can choose 
                # any value and experiment with it
                fps = 60.0
                
                # Creating a VideoWriter object
                out = cv2.VideoWriter(filename, codec, fps, resolution)

                # screen_record_process = Process(target=screen_record, args=(team, trial, recorder, lock))
                # detect_pause_change_process = Process(target=detect_pause_change, args=(lock, 25))
                # screen_record_process.start()
                # detect_pause_change_process.start()
                # screen_record_process.join()
                # recorder.start_recording(f"{team}_{trial}.mp4", 20)
                # subprocess.Popen(["./scoring_playback.sh", team, trial])
                # # Create an Empty window
                
                # sleep(25)
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
                    # # Optional: Display the recording screen
                    # cv2.imshow('Live', frame)
                    
                    # if cv2.waitKey(1) == ord('q'):
                    #     break
                # recorder.stop_recording()
                os.system(f"mv {team}_{trial}.avi {os.path.join('recordings', team, trial, f'{team}_{trial}.avi')}")
    for container in team_containers.values():
        print("Stopping container",container.name)
        container.stop()
    print("Done recording trials")
                
                

def main():
    team_names = get_team_names()
    trial_names = get_trial_names(team_names)
    final_scores = get_total_scores(team_names, trial_names)
    with open("ARIAC_results.csv", "w") as file:
        file.write("Leaderboard:\n\n")
        for team,score in final_scores.items():
            file.write(f"{team},{score}\n")

        file.write("\n\n\nScore Breakdown:\n\n")
        for trial in trial_names:
            file.write(f"{trial}:\n")
            order_ids = [order.order_id for order in get_order_information(trial)]
            file.write("Team,"+",".join([f"Order {order_ids.index(order_id)}({order_id}) Score,Order {order_ids.index(order_id)}({order_id}) Duration" for order_id in order_ids])+",trial_score\n")
            trial_info = score_trial(trial, create_graphs=True)
            for team in team_names:
                file.write(team+",")
                line = []
                for order_id in order_ids:
                    try:
                        line.append(str(trial_info.team_submissions[team].order_submissions[order_id].raw_score))
                    except:
                        line.append("N/A")
                    try:
                        line.append(str(trial_info.team_submissions[team].order_submissions[order_id].completion_duration))
                    except:
                        line.append("N/A")   
                line.append(str(trial_info.trial_scores[team]))
                file.write(",".join(line)+"\n")
            file.write("\n\n")
     
    # # Visualizing results
    # if not os.path.exists("graphs"):
    #     os.mkdir("graphs")
    # # Bar chart showing final scores
    # plt.bar(final_scores.keys(), final_scores.values(), 
    #     width = 0.4)
    # final_scores_vals = [round(val,3) for val in final_scores.values()]
    # addlabels(team_names, final_scores_vals)
    # plt.xlabel("Team")
    # plt.ylabel("Final Scores")
    # plt.title("ARIAC RESULTS")
    # plt.savefig("graphs/final_scores.png")
    # plt.clf()
    
    # # Bar chart showing final raw scores
    # raw_scores = total_raw_scores_by_team(team_names, trial_names)
    # plt.bar(raw_scores.keys(), raw_scores.values(), 
    #     width = 0.4)
    # final_scores_vals = [round(val,3) for val in raw_scores.values()]
    # addlabels(team_names, final_scores_vals)
    # plt.xlabel("Team")
    # plt.ylabel("Final Raw Scores")
    # plt.title("Total Raw Scores")
    # plt.savefig("graphs/final_raw_scores.png")
    # plt.clf()
    
    # # Multiple lines per trial
    # all_trial_scores = get_trial_scores_by_team(team_names, trial_names)
    # x = [i+1 for i in range(len(trial_names))]
    # for team in team_names:
    #     plt.plot(x, all_trial_scores[team], label = team, marker='o')
    # plt.xlabel("Trial")
    # plt.ylabel("Score")
    # plt.title("Trial Scores")
    # plt.xticks([i+1 for i in range(len(trial_names))],trial_names,rotation=30)
    # plt.legend()
    # plt.subplots_adjust(bottom=0.23)
    # plt.savefig("graphs/trial_scores.png")
    # plt.clf()
    
    # # Bar graph for each trial
    # for trial in trial_names:
    #     plt.bar(team_names, [all_trial_scores[team][trial_names.index(trial)] for team in team_names], 
    #         width = 0.4)
    #     addlabels(team_names, [round(all_trial_scores[team][trial_names.index(trial)],3) for team in team_names])
    #     plt.xlabel("Team")
    #     plt.ylabel("Score")
    #     plt.title(f"{trial} Scores")
    #     plt.savefig(f"graphs/{trial}_scores.png")
    #     plt.clf()
    
    # # Shows how the final scores increased over time
    # cumulative_totals_by_team = {team : [sum(all_trial_scores[team][:i]) for i in range(1,len(trial_names)+1)] for team in all_trial_scores.keys()}
    # x = [i+1 for i in range(len(trial_names))]
    # for team in team_names:
    #     plt.plot(x, cumulative_totals_by_team[team], label = team, marker='o')
    # plt.xlabel("Trial")
    # plt.ylabel("Score Up To This Point")
    # plt.title("Cumulative Trial Scores")
    # plt.xticks([i+1 for i in range(len(trial_names))],trial_names,rotation=30)
    # plt.legend()
    # plt.savefig("graphs/cumulative_scores.png")
    # plt.clf()
    
    # # Generate per team graphs
    # for team in team_names:
    #     if not os.path.exists(os.path.join("graphs",team)):
    #         os.mkdir(os.path.join("graphs",team))
    #     for trial in trial_names:
    #         order_ids = [order.order_id for order in get_order_information(trial)]
    #         trial_info = score_trial(trial)
    #         trial_max_scores = get_max_scores_for_trial(team_names, trial)
    #         max_scores = [val for val in trial_max_scores.values()]
    #         trial_scores = []
    #         for order in order_ids:
    #             try:
    #                 trial_scores.append(int(trial_info.team_submissions[team].order_submissions[order].raw_score))
    #             except:
    #                 trial_scores.append(0.0)
    #         durations = []
    #         for order in order_ids:
    #             try:
    #                 durations.append("Duration: "+str(trial_info.team_submissions[team].order_submissions[order].completion_duration))
    #             except:
    #                 durations.append("ORDER NOT SUBMITTED")
    #         x = [f"Order_{order_ids.index(order_id)}({order_id})\n{durations[order_ids.index(order_id)]}" for order_id in order_ids]
    #         X_axis = np.arange(len(x)) 
    #         plt.bar(X_axis + 0.2, max_scores, 0.4, label = 'Maximum Score') 
    #         plt.bar(X_axis - 0.2, trial_scores, 0.4, label = 'Actual Score') 
    #         for i in range(len(x)):
    #             plt.text(i, max_scores[i],f"{int(trial_scores[i])}"+" "*13+f"{int(max_scores[i])}", ha = 'center')
    #         plt.xticks(X_axis, x) 
    #         plt.xlabel("Order") 
    #         plt.ylabel("Score") 
    #         plt.title(f"Raw Score per Order in {trial}")
    #         plt.gca().set_xbound(-0.5 ,1.5)
    #         plt.legend(loc=(1.01, 0))
    #         plt.subplots_adjust(right=0.73)
    #         plt.savefig(f"graphs/{team}/{trial}.png")
    #         plt.clf()
    # filter_best_trial_logs(team_names, trial_names)
    record_each_trial_log(team_names, trial_names)
    
    
if __name__ == "__main__":
    main()