from typing import Optional

class OrderInfo():
    def __init__(self, order_id: str, priority: bool, max_score: int):
        self.order_id = order_id
        self.priority = priority
        self.max_score = max_score

class OrderSubmission():
    def __init__(self, raw_score: int, completion_duration: float):
        self.completion_duration = completion_duration
        self.raw_score = raw_score

class TeamSubmission():
    def __init__(self, order_submissions : dict[str, Optional[OrderSubmission]], sensor_cost : int):
        self.sensor_cost = sensor_cost
        self.order_submissions = order_submissions

class TrialInfo():
    def __init__(self, trial_name: str, trial_scores: dict[str, float], team_submissions: dict[str, TeamSubmission], team_best_file_logs: dict[str, str]):
        self.trial_name = trial_name
        self.trial_scores = trial_scores
        self.team_submissions = team_submissions
        self.team_best_file_logs = team_best_file_logs
