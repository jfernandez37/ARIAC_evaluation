import os
from typing import Optional

import yaml

from structs import (
    OrderInfo,
    OrderSubmission,
    TeamSubmission,
    TrialInfo
)

from graphs import team_raw_score_graph


def get_order_information(trial: str) -> list[OrderInfo]:

    """Parses the trial configuration for a trial and returns all the order_ids

    Args:
        trial (str): trial name

    Returns:
        list[OrderInfo]: list of information about each order in the given trial
    """

    automated_eval_folder = os.path.abspath(os.path.join(__file__, "..", ".."))
    trial_config_path = os.path.join(automated_eval_folder, 'trials', trial + '.yaml')

    if not os.path.exists(trial_config_path):
        print(f'Trial config: {trial_config_path} not found')
        return []

    try:
        with open(trial_config_path, 'r', encoding='utf-8') as f:
            trial_config = yaml.safe_load(f)
    except (IOError, yaml.YAMLError):
        print(f'Unable to parse trial config: {trial_config_path}')

    try:
        orders = trial_config['orders']
    except KeyError:
        print(f'No orders in trial config: {trial_config_path}')

    info_list = []
    for order in orders:
        order_id: str = order['id']
        try:
            priority = order['priority']
        except KeyError:
            priority = False

        max_score = calculate_order_max_score(order)

        info_list.append(OrderInfo(order_id, priority, max_score))

    return info_list


def calculate_order_max_score(order: dict) -> int:
    """ Calculates the maximum score for an order 

    Args:
        order (dict): Snippet of trial yaml file for an order

    Returns:
        int: maximum possible score for the order
    """
    try:
        if order['type'] == 'kitting':
            num_parts = len(order['kitting_task']['products'])
            return 1 + 3 * num_parts + num_parts
        elif order['type'] == 'assembly':
            num_parts = len(order['assembly_task']['products'])
            return 3 * num_parts + num_parts
        elif order['type'] == 'combined':
            num_parts = len(order['combined_task']['products'])
            return 5 * num_parts + num_parts
    except KeyError:
        print('Unable to compute max score for order')

    return 0

def get_trial_raw_score(trial_log: str) -> Optional[int]:

    """Parses a trial log file and calculates the combined score for all orders

    Args:
        trial_log (str): trial log file path

    Returns:
        Optional[int]: raw score for all orders, None if unable to read trial log
    """

    try:
        with open(trial_log, 'r', encoding='utf-8') as file:
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
        with open(trial_log, 'r', encoding='utf-8') as file:
            lines = file.readlines()
    except IOError:
        print(f'Unable to open file: {trial_log}')
        return None

    return float(lines[6].split(":")[-1])


def get_best_run(team: str, trial: str) -> Optional[str]:

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
    automated_eval_folder = os.path.abspath(os.path.join(__file__, "..", ".."))

    try:
        team_all_logs =  os.scandir(os.path.join(automated_eval_folder, "logs", team))
    except FileNotFoundError:
        print(f'Team {team} does not have a log folder')
        return None

    trial_scores = []
    for log_folder in team_all_logs:
        folder_name = os.path.basename(log_folder)
        # Remove suffix i.e. {_n}
        suffix_length = len(folder_name.split("_")[-1]) + 1

        # Check if the current folder matches the trial
        if folder_name[:-suffix_length] == trial:
            log_file = os.path.join(log_folder, "trial_log.txt")

            if not os.path.exists(log_file):
                print(f'Log file {log_file} does not exist')
                continue

            raw_score = get_trial_raw_score(log_file)
            duration_time = get_trial_completion_time(log_file)
            trial_scores.append((log_folder.path, raw_score, duration_time))

    if not trial_scores:
        print(f'Team {team} has no completed runs for trial {trial}')
        return None

    # Sort trial first by raw_score, then by completion time
    trial_scores_sorted = sorted(trial_scores, key=lambda x:(-x[1], x[2]))

    return trial_scores_sorted[0][0]


def create_order_submissions(order_ids: list[str], trial_log: str) -> dict[str, Optional[OrderSubmission]]:

    """Parse a trial log file and create an OrderSubmission for each order id.

    Args:
        order_ids (list[str]): list of order ids for the trial
        trial_log (str): path of a the log file for a trial run

    Returns:
        dict[str, Optional[OrderSubmission]]: order submissions for each id
    """

    order_submissions: dict[str, Optional[OrderSubmission]] = {}

    try:
        with open(trial_log, 'r', encoding='utf-8') as file:
            lines = file.readlines()
    except IOError:
        print(f'Unable to open file: {trial_log}')
        return order_submissions

    # Get only order summary section of trial log
    start = [("Order Summary" in line) for line in lines].index(True) + 2
    end = [("Order Details" in line) for line in lines].index(True) - 2
    summary = lines[start:end]

    for order_id in order_ids:
        for i, line in enumerate(summary):
            if not order_id in line:
                continue

            try:
                score = int(summary[i + 5].split(":")[-1])
                completion_duration = float(summary[i+7].split(":")[-1])
                submission = OrderSubmission(score, completion_duration)
            except (ValueError, IndexError):
                submission = None

            break

        order_submissions[order_id] = submission

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
        with open(sensor_file, 'r', encoding='utf-8') as file:
            lines = file.readlines()
    except IOError:
        print(f'Unable to open file: {sensor_file}')
        return None

    try:
        return int(lines[15].split("$")[-1])
    except ValueError:
        print('Unable to read cost from file')
        return None


def score_trial(trial: str, team_names: list[str], wc: float=1.0, wt: float=1.0) -> TrialInfo:
    """ Scores the trial for all teams with logs for that trial

    Args:
        trial (str): trial name
        wc (float, optional): Weighting coefficient for sensor cost. Defaults to 1.0.
        wt (float, optional): Weighting coefficient for execution speed. Defaults to 1.0.
        create_graphs (bool, optional): Flag to control whether or not to create graphs. Defaults to False.

    Returns:
        TrialInfo: information about the score of the trial.
    """
    # Get all orders from the trial config file
    order_info = get_order_information(trial)

    # Get team names from competitor configs
    # team_names = get_team_names()

    # Create TeamSubmission for each team
    submissions : dict[str, TeamSubmission] = {}

    for team in team_names:
        best_run_folder = get_best_run(team, trial)

        if best_run_folder is None:
            continue

        trial_log = os.path.join(best_run_folder, "trial_log.txt")

        order_ids = [i.order_id for i in order_info]

        orders_submissions = create_order_submissions(order_ids, trial_log)

        sensor_cost = get_sensor_cost(best_run_folder)

        if sensor_cost is None:
            print(f'ERROR: Unable to create submission for team: {team}')
            continue

        submissions[team] = TeamSubmission(orders_submissions, sensor_cost)

    # Calculate average cost
    costs: list[int] = []
    for team_submission in submissions.values():
        costs.append(team_submission.sensor_cost)

    try:
        average_cost = sum(costs)/len(costs)
    except ZeroDivisionError:
        average_cost = 0

    # Calculate average submission duration for each order
    average_order_durations: dict[str, float] = {}
    for order in order_info:
        durations: list[float] = []

        for team_submission in submissions.values():
            orders_sub = team_submission.order_submissions[order.order_id]
            if orders_sub is not None:
                durations.append(orders_sub.completion_duration)

        try:
            average_order_durations[order.order_id] = sum(durations)/len(durations)
        except ZeroDivisionError:
            average_order_durations[order.order_id] = 0

    # Calculate trial score for each team
    trial_scores = {}
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

            try:
                efficiency_factor = wt * (average_order_durations[order.order_id]/orders_sub.completion_duration)
            except ZeroDivisionError:
                continue

            trial_score += (priority_multiplier * efficiency_factor * orders_sub.raw_score)

        cost_factor = wc * (average_cost/submission.sensor_cost)

        trial_score *= cost_factor
        trial_scores[team] = trial_score

    return TrialInfo(trial, trial_scores, submissions, {team : get_best_run(team, trial) for team in team_names})

def create_graphs(trial_info: TrialInfo):
    orders = get_order_information(trial_info.trial_name)

    automated_eval_folder = os.path.abspath(os.path.join(__file__, "..", ".."))
    graphs_folder = os.path.join(automated_eval_folder, 'scoring', 'graphs')

    if not os.path.exists(graphs_folder):
        os.mkdir(graphs_folder)

    for team, submission in trial_info.team_submissions.items():
        # Generate raw score graph
        team_graph_folder = os.path.join(graphs_folder, team)
        if not os.path.exists(team_graph_folder):
            os.mkdir(team_graph_folder)

        team_raw_score_graph(trial_info.trial_name, team, orders, list(submission.order_submissions.values()), team_graph_folder)

def log_results(trial_info: TrialInfo):
    print(f'Results for trial: {trial_info.trial_name}')

    for team_name, team_score in trial_info.trial_scores.items():
        print(f'\tScore for team {team_name}: {team_score}')