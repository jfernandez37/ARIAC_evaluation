import os
from copy import copy
import sys
import getopt
import subprocess

CWD = os.getcwd()
HOME_DIR = os.path.expanduser("~")
NUM_ITERATIONS_PER_TRIAL = 1

TEAM_NAMES = [file.path.split("/")[-1] for file in os.scandir(f"{CWD}/logs/") if file.is_dir()]
TRIAL_NAMES = list(set([(file.path.split("/")[-1]).split("_")[0]  for file in os.scandir(f"{CWD}/logs/{TEAM_NAMES[0]}") if file.is_dir()]))
TRIAL_NAMES = [file.replace(".yaml","") for file in os.listdir(CWD+"/trials") if ".yaml" in file]

AVERAGE_SENSOR_COST = 0
COST_WEIGHT = 1
TIME_WEIGHT = 1
FILTER = False

arg_list = sys.argv[1:]
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

ALL_SCORES = {team_name : {trial : [{"orders":[]} for _ in range(NUM_ITERATIONS_PER_TRIAL)] for trial in TRIAL_NAMES} for team_name in TEAM_NAMES}
for team_name in TEAM_NAMES: 
    ALL_SCORES[team_name]["trial_scores"] = []

for team_name in TEAM_NAMES:
    for trial_name in TRIAL_NAMES:
        trial_nums = sorted([int((file.path.split("/")[-1]).split("_")[-1]) for file in os.scandir(f"{CWD}/logs/{team_name}") if file.is_dir() and trial_name in file.path.split("/")[-1]])
        if NUM_ITERATIONS_PER_TRIAL > len(trial_nums):
            print(f"ERROR: NUM_ITERATIONS ({NUM_ITERATIONS_PER_TRIAL}) IS GREATER THAN THE NUMBER OF TRIALS RUN")
            quit()
        for i in range(1, NUM_ITERATIONS_PER_TRIAL+1):
            equal_lines = 0
            order_info = {}
            trial_num = trial_nums[-1*i]
            trial_log_file_path = CWD+f"/logs/{team_name}/{trial_name}_{trial_num}/trial_log.txt"
            if not os.path.isfile(trial_log_file_path):
                continue
            with open(trial_log_file_path,"r") as file:
                for line in file:
                    if equal_lines == 2 and ":" in line:
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
                    elif ":" in line and equal_lines == 4:
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
            with open(sensor_cost_file,"r") as file:
                for line in file:
                    if "Total sensor cost is: $" in line:
                        info = line.split("$")
                        while "\n" in info[1]:
                            info[1] = info[1].replace("\n","")
                        ALL_SCORES[team_name]["sensor_cost"] = int(float(info[1]))
        order_sums = []
        for i in range(NUM_ITERATIONS_PER_TRIAL):
            try:
                order_task_sum = sum([d["actual_task_score"] for d in ALL_SCORES[team_name][trial_name][i]["orders"]])
                order_sums.append(order_task_sum)
            except:
                pass
            
        maximum_order_sum = max(order_sums)
        if order_sums.count(maximum_order_sum)==1:
            ALL_SCORES[team_name][trial_name] = ALL_SCORES[team_name][trial_name][order_sums.index(maximum_order_sum)]
            ALL_SCORES[team_name][trial_name]["best_trial"] = trial_nums[-1-(NUM_ITERATIONS_PER_TRIAL-(order_sums.index(maximum_order_sum)+1))]
        else:
            times = [ALL_SCORES[team_name][trial_name][i]["completion_time"] for i in range(NUM_ITERATIONS_PER_TRIAL)]
            ALL_SCORES[team_name][trial_name] = ALL_SCORES[team_name][trial_name][times.index(min(times))]
            ALL_SCORES[team_name][trial_name]["best_trial"] = trial_nums[-1-(NUM_ITERATIONS_PER_TRIAL-(times.index(min(times))+1))]
total_sensor_cost = sum([ALL_SCORES[team_name]["sensor_cost"] for team_name in TEAM_NAMES])
AVERAGE_SENSOR_COST = total_sensor_cost / len(TEAM_NAMES)
        
    
with open("ARIAC_RESULTS.csv",'w') as results_file:
    results_file.write("Average sensor cost: "+str(AVERAGE_SENSOR_COST)+"\n"*3)
    
    results_file.write("Order information:\n")
    for trial_name in TRIAL_NAMES:
        num_orders_in_trial = 0
        average_order_times = []
        for i in range(len(ALL_SCORES[TEAM_NAMES[0]][trial_name]["orders"])):
            num_orders_in_trial+=1
            total_order_time = 0
            for team_name in TEAM_NAMES:
                total_order_time+=ALL_SCORES[team_name][trial_name]["orders"][i]["submission_duration"]
            average_order_times.append(total_order_time / len(TEAM_NAMES))
        results_file.write("Trial_name: "+trial_name+"\n")
        for i in range(1,num_orders_in_trial+1):
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
                trial_score += (TIME_WEIGHT * average_order_times[i] / ALL_SCORES[team_name][trial_name]['orders'][i]['submission_duration']) * ALL_SCORES[team_name][trial_name]['orders'][i]['actual_task_score']
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
    for team_score in final_scores[::-1]:
        results_file.write(f"{place},{team_score[0]},{team_score[1]}\n")
        place+=1
print(f"Results saved in {CWD}/ARIAC_RESULTS.csv")

if not FILTER:
    quit()
if not os.path.exists(HOME_DIR+"/original_state_logs"):
    os.system(f"mkdir {HOME_DIR}/original_state_logs")
commands = []
subprocesses = []
for team_name in TEAM_NAMES:
    for trial_name in TRIAL_NAMES:
        os.system(f"mkdir {CWD}/logs/{team_name}/best_{trial_name}")
        commands.append(["./filter_state_log.sh", f"{CWD}/logs/{team_name}/{trial_name}_{ALL_SCORES[team_name][trial_name]['best_trial']}/state.log", f"{CWD}/logs/{team_name}/best_{trial_name}/state.log"])
for command in commands:
    subprocesses.append(subprocess.Popen(command))
print("Filtering state.log" + ("" if len(commands)<=1 else "s") + "...")
end_codes = [s.wait() for s in subprocesses]
print(f"Saved state log" + ("" if len(commands)<=1 else "s")+"\n\nTo view recordings of the best trial run for a team, run this command: ")
print("./playback_trial {team_name} best_{trial_name}")