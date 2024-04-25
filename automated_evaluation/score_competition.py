from score_trial import (
    score_trial, 
    get_team_names,
    get_order_information
)
import os
import matplotlib.pyplot as plt 

def get_trial_names(team_names: list[str]) -> list[str]:
    """Parses the logs folder of each team found to find all the trials which have been run.

    Returns:
        list[str]: list of trial names
    """
    trial_names = []
    for team in team_names:
        for file in os.scandir(os.path.join(os.getcwd(),"logs",team)):
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

def addlabels(x,y):
    for i in range(len(x)):
        plt.text(i, y[i], y[i], ha = 'center')

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
            trial_info = score_trial(trial)
            for team in team_names:
                file.write(team+",")
                line = []
                for order_id in order_ids:
                    try:
                        line.append(str(trial_info.team_submissions[team].order_submissions[order_id].score))
                    except:
                        line.append("0")
                    try:
                        line.append(str(trial_info.team_submissions[team].order_submissions[order_id].completion_duration))
                    except:
                        line.append("0")   
                line.append(str(trial_info.trial_scores[team]))
                file.write(",".join(line)+"\n")
            file.write("\n\n")
     
    # Visualizing results
    if not os.path.exists("graphs"):
        os.mkdir("graphs")
    # Bar chart showing final scores
    plt.bar(final_scores.keys(), final_scores.values(), 
        width = 0.4)
    final_scores_vals = [round(val,3) for val in final_scores.values()]
    addlabels(team_names, final_scores_vals)
    plt.xlabel("Team")
    plt.ylabel("Final Scores")
    plt.title("ARIAC RESULTS")
    plt.savefig("graphs/final_scores.png")
    plt.clf()
    
    # Multiple lines per trial
    all_trial_scores = get_trial_scores_by_team(team_names, trial_names)
    x = [i+1 for i in range(len(trial_names))]
    for team in team_names:
        plt.plot(x, all_trial_scores[team], label = team, marker='o')
    plt.xlabel("Trial")
    plt.ylabel("Score")
    plt.title("Trial Scores")
    plt.xticks([i+1 for i in range(len(trial_names))],trial_names,rotation=30)
    plt.legend()
    plt.subplots_adjust(bottom=0.23)
    plt.savefig("graphs/trial_scores.png")
    plt.clf()
    
    # Bar graph for each trial
    for trial in trial_names:
        plt.bar(team_names, [all_trial_scores[team][trial_names.index(trial)] for team in team_names], 
            width = 0.4)
        addlabels(team_names, [round(all_trial_scores[team][trial_names.index(trial)],3) for team in team_names])
        plt.xlabel("Team")
        plt.ylabel("Score")
        plt.title(f"{trial} Scores")
        plt.savefig(f"graphs/{trial}_scores.png")
        plt.clf()
    
    # Shows how the final scores increased over time
    cumulative_totals_by_team = {team : [sum(all_trial_scores[team][:i]) for i in range(1,len(trial_names)+1)] for team in all_trial_scores.keys()}
    x = [i+1 for i in range(len(trial_names))]
    for team in team_names:
        plt.plot(x, cumulative_totals_by_team[team], label = team, marker='o')
    plt.xlabel("Trial")
    plt.ylabel("Score Up To This Point")
    plt.title("Cumulative Trial Scores")
    plt.xticks([i+1 for i in range(len(trial_names))],trial_names,rotation=30)
    plt.legend()
    plt.savefig("graphs/cumulative_scores.png")
    
    
    
if __name__ == "__main__":
    main()