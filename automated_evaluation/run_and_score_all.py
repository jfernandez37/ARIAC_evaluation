import os
from copy import copy
import customtkinter as ctk
from tkinter import *
from functools import partial
import subprocess

CWD = os.getcwd()
HOME_DIR = os.path.expanduser("~")
NUM_ITERATIONS_PER_TRIAL = 1

TEAM_NAMES = [file.replace(".yaml","") for file in os.listdir(CWD+"/competitor_configs") if ".yaml" in file]
TRIAL_NAMES = [file.replace(".yaml","") for file in os.listdir(CWD+"/trials") if ".yaml" in file]
ALL_SCORES = {team_name : {trial : [{"orders":[]} for _ in range(NUM_ITERATIONS_PER_TRIAL)] for trial in TRIAL_NAMES} for team_name in TEAM_NAMES}

AVERAGE_SENSOR_COST = 0
COST_WEIGHT = 1
TIME_WIEGHT = 1

class Options_GUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.left_column, self.middle_column, self.right_column = 1,2,3
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(100, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(4, weight=1)

        self.team_vars = [ctk.StringVar() for _ in range(len(TEAM_NAMES))]
        self.trial_vars = [ctk.StringVar() for _ in range(len(TRIAL_NAMES))]
        for a in [self.team_vars, self.trial_vars]:
            for v in a:
                v.set("0")
        self.cost_weight_var = ctk.DoubleVar()
        self.cost_weight_var.set(1.0)
        self.time_weight_var = ctk.DoubleVar()
        self.time_weight_var.set(1.0)
        self.num_iter_var = ctk.IntVar()
        self.num_iter_var.set(1.0)

        self.team_selections = []
        self.trial_selections = []
        self.cost_weight_selection = 0.0
        self.time_weight_selection = 0.0
        self.num_iter_selection = 0.0

        for i in range(len(self.team_vars)):
            cb = ctk.CTkCheckBox(self, text=TEAM_NAMES[i], variable=self.team_vars[i], onvalue="1", offvalue="0", height=1, width=20)
            cb.grid(column = self.left_column, row = i+1, sticky=NW, padx = 25)
        select_all_teams_button = ctk.CTkButton(self, text="Select all teams", command=partial(self.select_all, self.team_vars))
        select_all_teams_button.grid(column = self.left_column, row = len(self.team_vars)+1)

        for i in range(len(self.trial_vars)):
            cb = ctk.CTkCheckBox(self, text=TRIAL_NAMES[i], variable=self.trial_vars[i], onvalue="1", offvalue="0", height=1, width=20)
            cb.grid(column = self.right_column, row = i+1, sticky=NW, padx = 25)
        select_all_trials_button = ctk.CTkButton(self, text="Select all trials", command=partial(self.select_all, self.trial_vars))
        select_all_trials_button.grid(column = self.right_column, row = len(self.trial_vars)+1)
        
        self.cost_weight_label = ctk.CTkLabel(self, text="Cost weight = "+str(self.cost_weight_var.get()))
        self.cost_weight_label.grid(column = self.middle_column, row = 1)
        self.cost_weight_slider = ctk.CTkSlider(self,variable=self.cost_weight_var,from_=1.0, to=10.0, number_of_steps=19, orientation="horizontal")
        self.cost_weight_slider.grid(column = self.middle_column, row = 2)

        self.time_weight_label = ctk.CTkLabel(self, text="Time weight = "+str(self.time_weight_var.get()))
        self.time_weight_label.grid(column = self.middle_column, row = 3)
        self.time_weight_slider = ctk.CTkSlider(self,variable=self.time_weight_var,from_=1.0, to=10.0, number_of_steps=19, orientation="horizontal")
        self.time_weight_slider.grid(column = self.middle_column, row = 4)
        
        self.num_iter_label = ctk.CTkLabel(self, text="Number of iterations per trial per team = "+str(self.num_iter_var.get()))
        self.num_iter_label.grid(column = self.middle_column, row = 5)
        self.num_iter_slider = ctk.CTkSlider(self,variable=self.num_iter_var,from_=1, to=10, number_of_steps=9, orientation="horizontal")
        self.num_iter_slider.grid(column = self.middle_column, row = 6)

        self.cost_weight_var.trace_add('write', self.update_cost_weight_label)
        self.time_weight_var.trace_add('write', self.update_time_weight_label)
        self.num_iter_var.trace_add('write', self.update_num_iter_label)

        self.save_button = ctk.CTkButton(self, text="Save selections", command=self.save_selections)
        self.save_button.grid(column = self.middle_column, pady = 50)

    def update_cost_weight_label(self,_,__,___):
        self.cost_weight_label.configure(text = "Cost weight = "+str(self.cost_weight_var.get()))
    
    def update_time_weight_label(self,_,__,___):
        self.time_weight_label.configure(text = "Time weight = "+str(self.time_weight_var.get()))
    
    def update_num_iter_label(self,_,__,___):
        self.num_iter_label.configure(text = "Number of iterations per trial per team = "+str(self.num_iter_var.get()))
    
    def select_all(self, l):
        for v in l:
            v.set("1")
    
    def save_selections(self):
        self.team_selections = [TEAM_NAMES[i] for i in range(len(TEAM_NAMES)) if self.team_vars[i].get()=="1"]
        self.trial_selections = [TRIAL_NAMES[i] for i in range(len(TRIAL_NAMES)) if self.trial_vars[i].get()=="1"]
        self.cost_weight_selection = self.cost_weight_var.get()
        self.time_weight_selection = self.time_weight_var.get()
        self.num_iter_selection = self.num_iter_var.get()
        self.destroy()

if __name__ == "__main__":
    setup_gui = Options_GUI()
    setup_gui.mainloop()
    if len(setup_gui.team_selections)>0:
        TEAM_NAMES = setup_gui.team_selections
    if len(setup_gui.trial_selections)>0:
        TRIAL_NAMES = setup_gui.trial_selections
    if setup_gui.time_weight_selection != 0.0:
        TIME_WIEGHT = setup_gui.time_weight_selection
    if setup_gui.cost_weight_selection != 0.0:
        COST_WEIGHT = setup_gui.cost_weight_selection
    if setup_gui.num_iter_selection != 0.0:
        NUM_ITERATIONS_PER_TRIAL = setup_gui.num_iter_selection
    nvidia_present = False
    try:
        subprocess.check_output('nvidia-smi')
        nvidia_present = True
        print("Nvidia card detected")
    except:
        print("No Nvidia card detected")

    os.system("rm -rf logs")
    for team_name in TEAM_NAMES:
        os.system(f"docker container rm {team_name} --force")
        os.system(f"./build_container.sh {team_name}" + (" nvidia" if nvidia_present else ""))
        for trial_name in TRIAL_NAMES:
            os.system(f"./run_trial.sh {team_name} {trial_name} {NUM_ITERATIONS_PER_TRIAL}")
        print("="*50)
        print("Completed all trials for team: "+team_name)
        print("="*50)
    
    for team_name in TEAM_NAMES:
        for trial_name in TRIAL_NAMES:
            for i in range(1, NUM_ITERATIONS_PER_TRIAL+1):
                equal_lines = 0
                order_info = {}
                trial_log_file_path = CWD+f"/logs/{team_name}/{trial_name}_{i}/trial_log.txt"
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
                sensor_cost_file = CWD+f"/logs/{team_name}/{trial_name}_{i}/sensor_cost.txt"
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
                ALL_SCORES[team_name][trial_name]["best_trial"] = order_sums.index(maximum_order_sum)+1
            else:
                times = [ALL_SCORES[team_name][trial_name][i]["completion_time"] for i in range(NUM_ITERATIONS_PER_TRIAL)]
                ALL_SCORES[team_name][trial_name] = ALL_SCORES[team_name][trial_name][times.index(min(times))]
                ALL_SCORES[team_name][trial_name]["best_trial"] = times.index(min(times))+1
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
                results_file.write(",".join([f"Order{i+1} (id: {ALL_SCORES[TEAM_NAMES[0]][trial_name]['orders'][i]['order_id']}) average time: {average_order_times[i]}" for i in range(num_orders_in_trial)]))
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
                    trial_score += (TIME_WIEGHT * average_order_times[i] / ALL_SCORES[team_name][trial_name]['orders'][i]['submission_duration']) * ALL_SCORES[team_name][trial_name]['orders'][i]['actual_task_score']
                trial_score *= COST_WEIGHT * AVERAGE_SENSOR_COST / ALL_SCORES[team_name]["sensor_cost"]
                results_file.write(f"{trial_score}")
                results_file.write("\n")
            results_file.write("\n"*3)
    
    if not os.path.exists(HOME_DIR+"/original_state_logs"):
        os.system(f"mkdir {HOME_DIR}/original_state_logs")
    for team_name in TEAM_NAMES:
        for trial_name in TRIAL_NAMES:
            if not os.path.exists(HOME_DIR+f"/original_state_logs/{team_name}/{trial_name}"):
                os.system(f"mkdir -p {HOME_DIR}/original_state_logs/{team_name}/{trial_name}")
            print(f"Waiting for {CWD}/logs/{team_name}{trial_name}_{ALL_SCORES[team_name][trial_name]['best_trial']}/state.log to exist...")
            while not os.path.exists(f"{CWD}/logs/{team_name}/{trial_name}_{ALL_SCORES[team_name][trial_name]['best_trial']}/state.log"):
                pass
            print("State.log found")
            os.system(f"mv {CWD}/logs/{team_name}/{trial_name}_{ALL_SCORES[team_name][trial_name]['best_trial']}/state.log {HOME_DIR}/original_state_logs/{team_name}/{trial_name}/state.log")
            print(f"Originial state.log moved to {HOME_DIR}/original_state_logs/{team_name}/{trial_name}/state.log\nFiltering state.log...")
            os.system(f"gz log -e -f {HOME_DIR}/original_state_logs/{team_name}/{trial_name}/state.log -z 100 --filter *.pose/*.pose > {CWD}/logs/{team_name}/{trial_name}_{ALL_SCORES[team_name][trial_name]['best_trial']}/state.log")
            print(f"Put new state.log in {CWD}/logs/{trial_name}_{ALL_SCORES[team_name][trial_name]['best_trial']}/state.log")