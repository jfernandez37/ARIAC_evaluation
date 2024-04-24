from score_trial import (
    score_trial, 
    get_team_names,
    get_order_information,
    TrialInfo,
    TeamSubmission,
    OrderInfo,
    OrderSubmission
)
import os
import matplotlib.pyplot as plt 

def get_trial_names() -> list[str]:
    """Parses the logs folder of the first team found to find all the trials which have been run.

    Returns:
        list[str]: list of trial names
    """
    trial_names = []
    for file in os.scandir(os.path.join(os.getcwd(),"logs",get_team_names()[0])):
        if file.is_dir():
            trial_names.append("_".join(os.path.basename(file).split("_")[:-1]))
    return list(set(sorted(trial_names)))

def get_total_scores(team_names: list[str],trial_names: list[str])->dict[str,float]:
    final_scores_by_team = {team : 0 for team in team_names}
    for trial in trial_names:
        trial_info = score_trial(trial)
        for team in team_names:
            final_scores_by_team[team] += trial_info.trial_scores[team]
    return {k: v for k, v in sorted(final_scores_by_team.items(), key=lambda item: -item[1])}

def get_trial_scores_by_team(team_names: list[str],trial_names: list[str])->dict[str,list[float]]:
    all_trial_scores = {team: [] for team in team_names}
    for trial in trial_names:
        trial_info = score_trial(trial)
        for team in team_names:
            all_trial_scores[team].append(trial_info.trial_scores[team])
    return all_trial_scores

def main():
    team_names = get_team_names()
    trial_names = get_trial_names()
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
            trial_info = score_trial(trial)
            for team in team_names:
                file.write(team+",")
                line = []
                for order_id in order_ids:
                    line.append(str(trial_info.team_submissions[team].order_submissions[order_id].score))
                    line.append(str(trial_info.team_submissions[team].order_submissions[order_id].completion_duration))
                line.append(str(trial_info.trial_scores[team]))
                file.write(",".join(line)+"\n")
            file.write("\n\n")
     
    # Visualizing results
    all_trial_scores = get_trial_scores_by_team(team_names, trial_names)
    x = [i+1 for i in range(len(trial_names))]
    for team in team_names:
        plt.plot(x, all_trial_scores[team], label = team)
    plt.legend() 
    plt.show()
    
    
if __name__ == "__main__":
    main()