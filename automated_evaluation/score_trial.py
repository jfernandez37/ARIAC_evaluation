import os
from copy import copy
import sys
import getopt
import subprocess
from math import inf
import yaml
import argparse


class OrderSubmission():
    def __init__(self, order_id, submitted, priority, time_to_complete, score):
        self.order_id = order_id
        self.submitted = submitted
        self.priority = priority
        self.time_to_complete = time_to_complete
        self.score = score

class TeamSubmission():
    def __init__(self, orders : list[OrderSubmission], cost : int):
        self.cost = cost
        self.orders = orders

class CombinedTeamScores():
    def __init__(self, submission_durations, scores):
        self.submission_durations = submission_durations
        self.scores = scores
        
def get_trial_raw_score(trial_file):
    with open(trial_file, "r") as file:
        lines = file.readlines()
        start = [("Order Summary" in line) for line in lines].index(True) + 2
        end = [("Order Details" in line) for line in lines].index(True) - 2

    summary = lines[start:end]
    
    raw_score = 0
    for i in range(len(summary)//8):
        raw_score += int(summary[i*8 + 5].split(":")[-1]) 
        
    return raw_score

def get_trial_completion_time(trial_file):
    with open(trial_file, "r") as file:
        lines = file.readlines()
        if len(lines) > 7:
            return float(lines[6].split(":")[-1])
        else:
            return inf
        
def get_order_ids(trial_name):
    order_ids = []
    if os.path.exists(f"{os.getcwd()}/trials/{trial_name}.yaml"):
        with open(f"{os.getcwd()}/trials/{trial_name}.yaml") as f:
            yaml_dict = yaml.safe_load(f)
        for order in yaml_dict["orders"]:
            order_ids.append(order["id"])
    return order_ids

def get_team_names():
    return [file.path.split("/")[-1] for file in os.scandir(f"{os.getcwd()}/logs/") if file.is_dir()]
        
def get_best_trial(team_name, trial_name):
    all_trials = os.scandir(f"{os.getcwd()}/logs/{team_name}")
    trial_folder_names = [f for f in all_trials if os.path.basename(f)[:-2] == trial_name]
    
    trial_scores = []
    for folder in trial_folder_names:
        log_file = os.path.join(folder, "trial_log.txt")
        
        if os.path.exists(log_file):
            raw_score = get_trial_raw_score(log_file)
            duration_time = get_trial_completion_time(log_file)
            trial_scores.append((log_file,raw_score, duration_time))
        else:
            trial_scores.append(("", 0, inf))
    
    # Sort trial first by raw_score, then by completion time
    return sorted(trial_scores, key=lambda x:(-x[1], x[2]))[0][0]

def create_order_submissions(trial_file):
    order_submissions = []
    with open(trial_file, "r") as file:
        lines = file.readlines()
        start = [("Order Summary" in line) for line in lines].index(True) + 2
        end = [("Order Details" in line) for line in lines].index(True) - 2
        summary = lines[start:end]
        for i in range(len(summary)//8):
            order_id = summary[i*8].split(": ")[-1]
            submitted = summary[i*8+1].split(": ") == "yes"
            priority = summary[i*8 + 2].split(": ") == "yes"
            time_to_complete = float(summary[i*8+7].split(": ")[-1]) if summary[i*8+7].split(": ") != "N/A" else None
            score = int(summary[i*8 + 5].split(":")[-1])
        print(summary)
        order_submissions.append(OrderSubmission(order_id, submitted, priority, time_to_complete, score))
    return order_submissions

def get_sensor_cost(team_name, trial_name):
    with open(f"{os.getcwd()}/logs/{team_name}/{trial_name}_2/sensor_cost.txt") as file:
        lines = file.readlines()
    return int(lines[15].split("$")[-1])
        

def main(args):
    trial_name = args.trial_name
    w_c = args.w_c
    w_t = args.w_t
    order_ids = get_order_ids(trial_name)
    team_names = get_team_names()
    submissions : dict[str, TeamSubmission] = {}
    for team in team_names:
        best_trial = get_best_trial(team, trial_name)
        orders_submissions = create_order_submissions(best_trial)
        sensor_cost = get_sensor_cost(team, trial_name)
        submissions[team] = TeamSubmission(orders_submissions, sensor_cost)
    combined_team_scores : dict[str, CombinedTeamScores] = {}
    for id in order_ids:
        submission_durations = []
        scores = []
        for team in team_names:
            print(id)
            order_submission = [s for s in submissions[team].orders if s.order_id == id][0]
            order_submission : OrderSubmission
            if order_submission.submitted:
                submission_durations.append(order_submission.time_to_complete)
                scores.append(order_submission.score)
        combined_team_scores[id] = CombinedTeamScores(submission_durations, scores)
    tc_avg = sum([submissions[team].cost for team in team_names])/len(team_names)
    trial_scores : dict[str, float] = {}
    for team in team_names:
        trial_score = 0
        for order_id, combined_score in combined_team_scores.items():
            order_submission = [s for s in submissions[team].orders if s.order_id == order_id][0]
            if not order_submission.submitted:
                continue
            t_avg = sum(combined_score.submission_durations)/len(combined_score.submission_durations)
            cf = w_c*(tc_avg/submissions[team].cost)
            ef = w_t*(t_avg/order_submission.time_to_complete)
            pm = 3 if order_submission.priority else 1
            trial_score += pm * ef * cf * order_submission.score
        trial_scores[team] = trial_score
    print(trial_score)
    
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("trial_name")
    parser.add_argument("w_c", type=float, default=1.0)
    parser.add_argument("w_t", type=float, default=1.0)
    main(parser.parse_args())