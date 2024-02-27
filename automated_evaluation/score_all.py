import os
from copy import copy
import sys
import getopt
import subprocess

CWD = os.getcwd()
HOME_DIR = os.path.expanduser("~")
NUM_ITERATIONS_PER_TRIAL = 1

# Makes a list of all team names from the logs directory
TEAM_NAMES = [file.path.split("/")[-1] for file in os.scandir(f"{CWD}/logs/") if file.is_dir()]
# Makes a list of all trial names from first team's log directory
TRIAL_NAMES = list(set(["_".join((file.path.split("/")[-1]).split("_")[:-1])  for file in os.scandir(f"{CWD}/logs/{TEAM_NAMES[0]}") if file.is_dir() and "best" not in file.path.split("/")[-1]]))

# Initial values for parameters
AVERAGE_SENSOR_COST = 0
COST_WEIGHT = 1
TIME_WEIGHT = 1
FILTER = False

# List of all parameters passed in by the user
arg_list = sys.argv[1:]
# String of all options
options = "c:t:n:f:"
long_options = ["cost_weight=", "time_weight=", "num_iter=", "filter="]
try:
    # Parsing argument
    arguments, values = getopt.getopt(arg_list, options, long_options)
     
    # checking each argument
    for currentArgument, currentValue in arguments:
 
        if currentArgument in ("-c", "--cost_weight"):
            COST_WEIGHT = float(currentValue)
            print(f"Set cost weight to {COST_WEIGHT}")
             
        elif currentArgument in ("-t", "--time_weight"):
            TIME_WEIGHT = float(currentValue)
            print(f"Set time weight to {TIME_WEIGHT}")
             
        elif currentArgument in ("-n", "--num_iter"):
            NUM_ITERATIONS_PER_TRIAL = int(float(currentValue))
            print(f"Set num_iter to {NUM_ITERATIONS_PER_TRIAL}")
        
        elif currentArgument in ("-f", "--filter"):
            FILTER = "f" not in currentValue.lower()
            print(f"Filter set to {FILTER}")
except getopt.error as err:
    print (str(err))

# Dictionary with the strucure for all attempts of each trial for each team
ALL_SCORES = {team_name : {trial : [{"orders":[]} for _ in range(NUM_ITERATIONS_PER_TRIAL)] for trial in TRIAL_NAMES} for team_name in TEAM_NAMES}
#Adds a list of trial scores for each of the teams.
for team_name in TEAM_NAMES: 
    ALL_SCORES[team_name]["trial_scores"] = []

for team_name in TEAM_NAMES:
    for trial_name in TRIAL_NAMES:
        # trial nums = sorted list of trial numbers for the trial trial_name
        trial_nums = sorted([int((file.path.split("/")[-1]).split("_")[-1]) for file in os.scandir(f"{CWD}/logs/{team_name}") if file.is_dir() and trial_name in file.path.split("/")[-1] and "best" not in file.path.split("/")[-1]])
        if NUM_ITERATIONS_PER_TRIAL > len(trial_nums):
            print(f"ERROR: NUM_ITERATIONS ({NUM_ITERATIONS_PER_TRIAL}) IS GREATER THAN THE NUMBER OF TRIALS RUN ({len(trial_nums)})")
            quit()
        for i in range(1, NUM_ITERATIONS_PER_TRIAL+1): # Loops through each trial run
            equal_lines = 0
            order_info = {}
            # Gets the trial name for the ith to last trial run
            trial_num = trial_nums[-1*i]
            trial_log_file_path = CWD+f"/logs/{team_name}/{trial_name}_{trial_num}/trial_log.txt"
            if not os.path.isfile(trial_log_file_path):
                continue
            with open(trial_log_file_path,"r") as file:
                # Loops through each line of the trial_log file. Converts it into a list
                for line in file:
                    if equal_lines == 2 and ":" in line: # Trial report
                        info = line.split(": ")
                        
                        info = [s.lower() for s in info]
                        while "\t" in info[0]:
                            info[0] = info[0].replace("\t","")
                        while " " in info[0]:
                            info[0] = info[0].replace(" ","_")
                        while "\n" in info[1]:
                            info[1] = info[1].replace("\n","")
                        try:
                            info[1] = int(info[1])
                        except:
                            try:
                                info[1] = float(info[1])
                            except:
                                pass
                        ALL_SCORES[team_name][trial_name][i-1][info[0]] = info[1]
                    elif "====" in line:
                        equal_lines +=1
                        if equal_lines>4:
                            break
                    elif ":" in line and equal_lines == 4: # Order report
                        if "order id" in line.lower():
                            order_info = {}
                        info = line.split(": ")
                        info = [s.lower() for s in info]
                        while "\t" in info[0]:
                            info[0] = info[0].replace("\t","")
                        while " " in info[0]:
                            info[0] = info[0].replace(" ","_")
                        while "\n" in info[1]:
                            info[1] = info[1].replace("\n","")
                        try:
                            info[1] = int(info[1])
                        except:
                            try:
                                info[1] = float(info[1])
                            except:
                                pass
                        order_info[info[0]] = (info[1] if info[0]!="order_id" else info[1].upper())
                        if info[0] == "submission_duration":
                            ALL_SCORES[team_name][trial_name][i-1]["orders"].append(copy(order_info))
            sensor_cost_file = CWD+f"/logs/{team_name}/{trial_name}_{trial_num}/sensor_cost.txt"
            with open(sensor_cost_file,"r") as file: # Gets the sensor cost for team team_name
                for line in file:
                    if "Total sensor cost is: $" in line:
                        info = line.split("$")
                        while "\n" in info[1]:
                            info[1] = info[1].replace("\n","")
                        ALL_SCORES[team_name]["sensor_cost"] = int(float(info[1]))
        order_sums = []
        # Gets the sum of each of the orders for each trial run
        for i in range(NUM_ITERATIONS_PER_TRIAL):
            try: 
                order_task_sum = sum([d["actual_task_score"] for d in ALL_SCORES[team_name][trial_name][i]["orders"]])
                order_sums.append(order_task_sum)
            except:
                pass
            
        maximum_order_sum = max(order_sums)
        if order_sums.count(maximum_order_sum)==1: # Runs if one run has a higher score than the others
            ALL_SCORES[team_name][trial_name] = ALL_SCORES[team_name][trial_name][order_sums.index(maximum_order_sum)]
            ALL_SCORES[team_name][trial_name]["best_trial"] = trial_nums[-1-(NUM_ITERATIONS_PER_TRIAL-(order_sums.index(maximum_order_sum)+1))]
        else: # If multiple trials have the best score, the one saved is the lowest time
            # Gets a list of indecies of each trial attempt where the sum of the trial scores is less than the maximum. The list is sorted in descending order
            bad_inds = sorted([i for i in range(len(ALL_SCORES[team_name][trial_name])) if sum([d["actual_task_score"] for d in ALL_SCORES[team_name][trial_name][i]["orders"]])!=maximum_order_sum])[::-1]
            temp_trial_nums = copy(trial_nums)
            # Loops through the bad indecies and deletes all bad trial attempts and the corresponding trial num 
            for i in bad_inds:
                del ALL_SCORES[team_name][trial_name][i]
                del trial_nums[trial_nums.index(temp_trial_nums[(-1*NUM_ITERATIONS_PER_TRIAL)+i])]
            times = [ALL_SCORES[team_name][trial_name][i]["completion_time"] for i in range(len(ALL_SCORES[team_name][trial_name]))]
            best_trial_ind = trial_nums[-1-(len(ALL_SCORES[team_name][trial_name])-(times.index(min(times))+1))]
            ALL_SCORES[team_name][trial_name] = ALL_SCORES[team_name][trial_name][times.index(min(times))]
            ALL_SCORES[team_name][trial_name]["best_trial"] = best_trial_ind
total_sensor_cost = sum([ALL_SCORES[team_name]["sensor_cost"] for team_name in TEAM_NAMES])
AVERAGE_SENSOR_COST = total_sensor_cost / len(TEAM_NAMES)
        
    
with open("ARIAC_RESULTS.csv",'w') as results_file: # Writes the result of the competition to a csv file
    results_file.write("Average sensor cost: $"+str(AVERAGE_SENSOR_COST)+"\n"*2)
    results_file.write("Team,Sensor cost\n")
    for team_name in TEAM_NAMES:
        results_file.write(f"{team_name},${ALL_SCORES[team_name]['sensor_cost']}\n")
    
    results_file.write("\n\nOrder information:\n")
    for trial_name in TRIAL_NAMES:
        num_orders_in_trial = 0
        average_order_times = []
        for i in range(len(ALL_SCORES[TEAM_NAMES[0]][trial_name]["orders"])):
            num_orders_in_trial+=1
            total_order_time = 0
            invalid_teams = 0
            for team_name in TEAM_NAMES:
                try:
                    total_order_time+=ALL_SCORES[team_name][trial_name]["orders"][i]["submission_duration"]
                except:
                    invalid_teams+=1
                    total_order_time+=0
            try:
                average_order_times.append(total_order_time / (len(TEAM_NAMES)-invalid_teams))
            except:
                average_order_times.append(10000)
        results_file.write("Trial_name: "+trial_name+"\n")
        results_file.write(",".join([f"Order {i+1} (id: {ALL_SCORES[TEAM_NAMES[0]][trial_name]['orders'][i]['order_id']}) average time: {average_order_times[i]}" for i in range(num_orders_in_trial)]))
        results_file.write('\n\nTeam name,')
        for i in range(1,len(ALL_SCORES[TEAM_NAMES[0]][trial_name]["orders"])+1):
            results_file.write(f"Order {i} id,Order {i} score,Order {i} submission duration,")
        results_file.write("Trial score")
        results_file.write('\n')
        for team_name in TEAM_NAMES:
            trial_score = 0
            results_file.write(team_name+",")
            for i in range(len(ALL_SCORES[team_name][trial_name]["orders"])):
                results_file.write(f"{ALL_SCORES[team_name][trial_name]['orders'][i]['order_id']},"+
                                f"{ALL_SCORES[team_name][trial_name]['orders'][i]['actual_task_score']},"+
                                f"{ALL_SCORES[team_name][trial_name]['orders'][i]['submission_duration']},")
                try:
                    trial_score += (TIME_WEIGHT * average_order_times[i] / ALL_SCORES[team_name][trial_name]['orders'][i]['submission_duration']) * ALL_SCORES[team_name][trial_name]['orders'][i]['actual_task_score']
                except:
                    trial_score += 0        
            trial_score *= COST_WEIGHT * AVERAGE_SENSOR_COST / ALL_SCORES[team_name]["sensor_cost"]
            ALL_SCORES[team_name]["trial_scores"].append(trial_score)
            results_file.write(f"{trial_score}")
            results_file.write("\n")
        results_file.write("\n"*3)
    results_file.write(",Leaderboard\nPosition,Team,Score\n")
    results_file.write(",".join(["="*10 for _ in range(3)])+"\n")
    final_scores = []
    for team_name in TEAM_NAMES:
        final_scores.append((team_name,sum(ALL_SCORES[team_name]["trial_scores"])))
    final_scores.sort(key = lambda x: x[1])
    place=1
    # Writes out the leaderboard by decending scores
    for team_score in final_scores[::-1]:
        results_file.write(f"{place},{team_score[0]},{team_score[1]}\n")
        place+=1
print(f"Results saved in {CWD}/ARIAC_RESULTS.csv")

if not FILTER: # Runs if the parameter to filter the log has an f in it
    quit()
commands = []
for team_name in TEAM_NAMES:
    for trial_name in TRIAL_NAMES:
        if not os.path.exists(f"{CWD}/logs/{team_name}/best_{trial_name}"): # Does so to not overwrite the original log file
            os.system(f"mkdir {CWD}/logs/{team_name}/best_{trial_name}")
        commands.append(["./filter_state_log.sh", f"{CWD}/logs/{team_name}/{trial_name}_{ALL_SCORES[team_name][trial_name]['best_trial']}/state.log", f"{CWD}/logs/{team_name}/best_{trial_name}/state.log"])
subprocesses = [subprocess.Popen(command) for command in commands] # Runs each of the filtering commands in parallel
print("Filtering state.log" + ("" if len(commands)<=1 else "s") + "...")
end_codes = [s.wait() for s in subprocesses] # Waits until all of the best state logs are filtered
print(f"Saved state log" + ("" if len(commands)<=1 else "s")+"\n\nTo view recordings of the best trial run for a team, run this command: ")
print("./playback_trial.sh {team_name} best_{trial_name}")