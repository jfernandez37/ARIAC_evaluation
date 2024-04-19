import os
import argparse

import yaml
import math

from typing import Optional

class OrderInfo():
    def __init__(self, order_id: str, priority: bool):
        self.order_id = order_id
        self.priority = priority

class OrderSubmission():
    def __init__(self, score: int, completion_duration: float):
        self.completion_duration = completion_duration
        self.score = score

class TeamSubmission():
    def __init__(self, order_submissions : dict[str, Optional[OrderSubmission]], sensor_cost : int):
        self.sensor_cost = sensor_cost
        self.order_submissions = order_submissions
        
def get_order_information(trial: str) -> list[OrderInfo]:
    
    """Parses the trial configuration for a trial and returns all the order_ids

    Args:
        trial (str): trial name

    Returns:
        list[OrderInfo]: list of information about each order in the given trial
    """
    
    trial_config = os.path.join(os.getcwd(), 'trials', trial_name + '.yaml')
    
    if not os.path.exists(trial_config):
        print(f'Trial config: {trial_config} not found')
        return []
        
    try:
        with open(f"{os.getcwd()}/trials/{trial_name}.yaml") as f:
            trial_info = yaml.safe_load(f)
    except (IOError, yaml.YAMLError):
        print(f'Unable to parse trial config: {trial_config}')
    
    try:
        orders = trial_info['orders']
    except KeyError:
        print(f'No orders in trial config: {trial_config}')
    
    info_list = []
    for order in orders:
        id: str = order['id']
        try:
            priority = order['priority']
        except KeyError:
            priority = False
            
        info_list.append(OrderInfo(id, priority))
    
    return info_list

def get_team_names() -> list[str]:
    
    """Parses the logs folder to find all the teams that have trial logs generated.

    Returns:
        list[str]: list of team names
    """
    
    logs_folder = os.path.join(os.getcwd(), "logs")
    
    return [os.path.basename(file) for file in os.scandir(logs_folder) if file.is_dir()]        

def get_trial_raw_score(trial_log: str) -> Optional[int]:
    
    """Parses a trial log file and calculates the combined score for all orders

    Args:
        trial_log (str): trial log file path 

    Returns:
        Optional[int]: raw score for all orders, None if unable to read trial log
    """
    
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
    raw_score = 0
    for i in range(len(summary)//8):
        raw_score += int(summary[(i * 8) + 5].split(":")[-1]) 
        
    return raw_score

def get_trial_completion_time(trial_log: str) -> Optional[float]:
    
    """Parses a trial log file and reads the time taken to complete the entire trial

    Args:
        trial_log (str): trial log file path 

    Returns:
        Optional[float]: completion time for the trial, None if unable to read trial log
    """
    
    try:
        with open(trial_log, "r") as file:
            lines = file.readlines()
    except IOError:
        print(f'Unable to open file: {trial_log}')
        return None    
    
    return float(lines[6].split(":")[-1])
            
def get_best_run(team: str, trial: str) -> str:
    
    """ Get the path of a log folder for the best run of a given trial 
    for a given team. Runs are ranked initially based on score, then
    by completion time.

    Args:
        team (str): team name
        trial (str): trial name

    Returns:
        str: path of folder for the best run
    """
    
    # Get all logs for team
    team_all_logs =  os.scandir(os.path.join(os.getcwd(), "logs", team))
    
    trial_scores = []
    for log_folder in team_all_logs:
        folder_name = os.path.basename(log_folder)
        # Remove suffix i.e. {_n}
        suffix_length = len(folder_name.split("_")[-1]) + 1
        
        # Check if the current folder matches the trial
        if folder_name[:-suffix_length] == trial:
            log_file = os.path.join(folder_name, "trial_log.txt")
            
            if not os.path.exists(log_file):
                print(f'Log file {log_file} does not exist')
                continue
            
            raw_score = get_trial_raw_score(log_file)
            duration_time = get_trial_completion_time(log_file)
            trial_scores.append((folder_name, raw_score, duration_time))
    
    # Sort trial first by raw_score, then by completion time
    trial_scores_sorted = sorted(trial_scores, key=lambda x:(-x[1], x[2]))

    return trial_scores_sorted[0][0]

def create_order_submissions(order_ids: list[str], trial_log: str) -> dict[str, Optional[OrderSubmission]]:
    
    """Parse a trial log file and create an OrderSubmssion for each order id. 

    Args:
        order_ids (list[str]): list of order ids for the trial
        trial_log (str): path of a the log file for a trial run

    Returns:
        dict[str, Optional[OrderSubmission]]: order submsissions for each id
    """
    
    order_submissions: dict[str, Optional[OrderSubmission]] = {}
    
    try:
        with open(trial_log, "r") as file:
            lines = file.readlines()
    except IOError:
        print(f'Unable to open file: {trial_log}')
        return order_submissions 
    
    # Get only order summary section of trial log
    start = [("Order Summary" in line) for line in lines].index(True) + 2
    end = [("Order Details" in line) for line in lines].index(True) - 2
    summary = lines[start:end]

    for id in order_ids:
        for i, line in enumerate(summary):
            if not id in line:
                continue
            
            try:
                score = int(summary[i + 5].split(":")[-1])
                completion_duration = float(summary[i+7].split(":")[-1])
                submission = OrderSubmission(score, completion_duration)
            except (ValueError, IndexError):
                submission = None
            
            break
                
        order_submissions[id] = submission
    
    return order_submissions

def get_sensor_cost(log_folder: str) -> Optional[int]:
    
    """Get sensor cost for a given run

    Args:
        log_folder (str): log folder for a trial run

    Returns:
        Optional[int]: sensor cost 
    """
    
    try:
        sensor_file = os.path.join(log_folder, "sensor_cost.txt")
        with open(sensor_file) as file:
            lines = file.readlines()
    except IOError:
        print(f'Unable to open file: {sensor_file}')
        return None
    
    try:
        return int(lines[15].split("$")[-1])
    except ValueError:
        print(f'Unable to read cost from file')
        return None
        

def main(trial: str, wc: float, wt: float):
    # Get all orders from the trial config file
    order_info = get_order_information(trial)
    
    # Get team names from competitor configs
    team_names = get_team_names()
    
    # Create TeamSubmssion for each team
    submissions : dict[str, TeamSubmission] = {}
    
    for team in team_names:
        best_run_folder = get_best_run(team, trial)
        
        trial_log = os.path.join(best_run_folder, "trial_log.txt")
        
        order_ids = [i.order_id for i in order_info]
        
        orders_submissions = create_order_submissions(order_ids, trial_log)
        
        sensor_cost = get_sensor_cost(best_run_folder)
        
        if sensor_cost is None:
            print(f'ERROR: Unable to create submssion for team: {team}')
            continue
        
        submissions[team] = TeamSubmission(orders_submissions, sensor_cost)
        
    # Calculate average cost
    costs: list[int] = []
    for team_submssion in submissions.values():
        costs.append(team_submssion.sensor_cost)
            
    average_cost = sum(costs)/len(costs)
    
    # Calculate average submssion duration for each order
    average_order_durations: dict[str, float] = {}
    for order in order_info:
        durations: list[float] = []
        
        for team_submssion in submissions.values():
            orders_sub = team_submssion.order_submissions[order.order_id]
            if orders_sub is not None:
                durations.append(orders_sub.completion_duration)

        average_order_durations[order.order_id] = sum(durations)/len(durations)
        
    # Calculate trial score for each team
    for team, submission in submissions.items():
        trial_score = 0
        for order in order_info:
            orders_sub = submission.order_submissions[order.order_id]
            
            if orders_sub is None:
                continue
            
            if not order.priority:
                priority_multiplier = 1
            else:
                priority_multiplier = 3
            
            efficiency_factor = time_weight * (average_order_durations[order.order_id]/orders_sub.completion_duration)
            
            trial_score += (priority_multiplier * efficiency_factor * orders_sub.score)
                
        cost_factor = cost_weight * (average_cost/submission.sensor_cost)
        
        trial_score *= cost_factor
        
        print(f'Trial score for team {team}: {trial_score:.2f}')
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Calculate the trial score for all competitors for a given trial")
    
    parser.add_argument("trial_name", help="The name of the trial to score")
    
    parser.add_argument("-c", "--cost-weight", type=float, default=1.0, )
    parser.add_argument("-t", "--time-weight", type=float, default=1.0)
    
    args = parser.parse_args()
    
    trial_name: str = args.trial_name
    cost_weight: float = args.cost_weight
    time_weight: float = args.time_weight
    
    main(trial_name, cost_weight, time_weight)