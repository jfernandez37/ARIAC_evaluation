import os
import yaml

from score_trial import score_trial


def get_competing_teams() -> list[str]:
    automated_eval_folder = os.path.abspath(os.path.join(__file__, "..", ".."))

    competitor_configs: list[str] = []
    for root, _, files in os.walk(os.path.join(automated_eval_folder, "competitor_configs")):
        for file in files:
            if not file.endswith('.yaml'):
                continue

            if "nist_competitor" in file:
                continue

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


def main():
    # Get list of team names from competitor_configs directory (exclude nist_competitor)
    competing_teams = get_competing_teams()

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


if __name__ == "__main__":
    main()