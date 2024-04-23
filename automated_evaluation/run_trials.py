import os
from copy import copy
import customtkinter as ctk
from tkinter import *
from functools import partial
import subprocess
from time import sleep
import docker

CWD = os.getcwd()
HOME_DIR = os.path.expanduser("~")
NUM_ITERATIONS_PER_TRIAL = 1

TEAM_NAMES = [file.replace(".yaml","") for file in os.listdir(CWD+"/competitor_configs") if ".yaml" in file]
TRIAL_NAMES = [file.replace(".yaml","") for file in os.listdir(CWD+"/trials") if ".yaml" in file]

def getContainers():
    dockerClient = docker.DockerClient()
    containersReturn = []
    containers = dockerClient.containers.list(all=True)
    for container in containers:
        containersReturn.append(container.name)
    return containersReturn

class Options_GUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        nvidia_present = False
        try:
            subprocess.check_output('nvidia-smi')
            nvidia_present = True
            print("Nvidia card detected")
        except:
            print("No Nvidia card detected")

            
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
        self.num_iter_var = ctk.IntVar()
        self.num_iter_var.set(1)
        self.max_iter_var = ctk.IntVar()
        self.max_iter_var.set(1)
        self.use_nvidia_var = ctk.StringVar()
        self.use_nvidia_var.set("1" if nvidia_present else "0")
        self.rebuild_containers_var = ctk.StringVar()
        self.rebuild_containers_var.set("0")
        self.update_trials_var = ctk.StringVar()
        self.update_trials_var.set("0")

        self.team_selections = []
        self.trial_selections = []
        self.num_iter_selection = 0
        self.max_iter_selection = 0
        self.use_nvidia = False
        self.rebuild_containers = False
        self.update_trials = False

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
        
        self.num_iter_label = ctk.CTkLabel(self, text="Number of iterations per trial per team = "+str(self.num_iter_var.get()))
        self.num_iter_label.grid(column = self.middle_column, row = 1)
        self.num_iter_slider = ctk.CTkSlider(self,variable=self.num_iter_var,from_=1, to=10, number_of_steps=9, orientation="horizontal")
        self.num_iter_slider.grid(column = self.middle_column, row = 2)
        
        self.max_iter_label = ctk.CTkLabel(self, text="Maximimum number of iterations per trial per team = "+str(self.num_iter_var.get()))
        self.max_iter_label.grid(column = self.middle_column, row = 3)
        self.max_iter_slider = ctk.CTkSlider(self,variable=self.max_iter_var,from_=1, to=20, number_of_steps=19, orientation="horizontal")
        self.max_iter_slider.grid(column = self.middle_column, row = 4)

        if nvidia_present:
            self.use_nvidia_cb = ctk.CTkCheckBox(self, variable=self.use_nvidia_var, onvalue="1", offvalue="0", state=NORMAL, text="Use NVIDIA in container")
            self.use_nvidia_cb.grid(column = self.middle_column, row = 5, sticky=NW, ipadx=15)
        
        self.rebuild_containers_cb = ctk.CTkCheckBox(self, variable=self.rebuild_containers_var, onvalue="1", offvalue="0", state=NORMAL, text="Rebuild containers")
        self.rebuild_containers_cb.grid(column = self.middle_column, row = 6, sticky=NW, ipadx=15)
        
        self.update_trials_cb = ctk.CTkCheckBox(self, variable=self.update_trials_var, onvalue="1", offvalue="0", state=NORMAL, text="Update trials")
        self.update_trials_cb.grid(column = self.middle_column, row = 7, sticky=NW, ipadx=15)
        
        self.spacing_label = ctk.CTkLabel(self, text=" "*(len(self.max_iter_label._text)+50))
        self.spacing_label.grid(column = self.middle_column, row=10)


        self.num_iter_var.trace_add('write', self.update_num_iter_label)
        self.max_iter_var.trace_add('write', self.update_max_iter_label)

        self.save_button = ctk.CTkButton(self, text="Run Competition", command=self.save_selections)
        self.save_button.grid(column = self.middle_column, pady = 50)
    
    def update_num_iter_label(self,_,__,___):
        self.num_iter_label.configure(text = "Number of iterations per trial per team = "+str(self.num_iter_var.get()))
        if self.max_iter_var.get()<self.num_iter_var.get():
            self.max_iter_var.set(self.num_iter_var.get())
    
    def update_max_iter_label(self,_,__,___):
        if self.max_iter_var.get()<self.num_iter_var.get():
            self.max_iter_var.set(self.num_iter_var.get())
        self.max_iter_label.configure(text = "Maximum number of iterations per trial per team = "+str(self.max_iter_var.get()))
    
    def select_all(self, l):
        for v in l:
            v.set("1")
    
    def save_selections(self):
        self.team_selections = [TEAM_NAMES[i] for i in range(len(TEAM_NAMES)) if self.team_vars[i].get()=="1"]
        self.trial_selections = [TRIAL_NAMES[i] for i in range(len(TRIAL_NAMES)) if self.trial_vars[i].get()=="1"]
        self.num_iter_selection = self.num_iter_var.get()
        self.max_iter_selection = self.max_iter_var.get()
        self.use_nvidia = self.use_nvidia_var.get()=="1"
        self.rebuild_containers = self.rebuild_containers_var.get()=="1"
        self.update_trials = self.update_trials_var.get()=="1"
        self.destroy()

if __name__ == "__main__":
    setup_gui = Options_GUI()
    setup_gui.mainloop()
    if 0 in [len(setup_gui.team_selections),len(setup_gui.trial_selections), setup_gui.num_iter_selection]:
        print("Exited out of GUI. Not running any trials.")
        quit()
    else:
        TEAM_NAMES = setup_gui.team_selections
        TRIAL_NAMES = setup_gui.trial_selections
        NUM_ITERATIONS_PER_TRIAL = setup_gui.num_iter_selection
        MAX_ITERATIONS_PER_TRIAL = setup_gui.max_iter_selection
        USE_NVIDIA = setup_gui.use_nvidia
        REBUILD_CONTAINERS = setup_gui.rebuild_containers
        UPDATE_TRIALS = (setup_gui.update_trials if not REBUILD_CONTAINERS else False)
    

    num_trials_run = 0
    for team_name in TEAM_NAMES:
        current_containers = getContainers()
        
        if REBUILD_CONTAINERS:
            if team_name in current_containers:
                os.system(f"docker container rm {team_name} --force")
                os.system(f"./build_container.sh {team_name}" + (" nvidia" if USE_NVIDIA else ""))
            else:
                print(f"{team_name} not found in existing docker containers. Building new container...")
                
        if team_name not in current_containers:
            os.system(f"./build_container.sh {team_name}" + (" nvidia" if USE_NVIDIA else ""))
        else:
            os.system(f"docker start {team_name}")
            
        if UPDATE_TRIALS:
            os.system(f"./update_trials.sh {team_name}")
            
        for trial_name in TRIAL_NAMES:
            trial_count = 0
            for _ in range(NUM_ITERATIONS_PER_TRIAL):
                print("\n"*5 + f"Running trial. {num_trials_run} have been run already." + "\n"*5)
                run_correctly = False
                while not run_correctly:
                    os.system(f"docker start {team_name}")
                    print("test")
                    os.system(f"./run_trial.sh {team_name} {trial_name} {1}")
                    trial_count+=1
                    trials_run = [file.path.split("/")[-1] for file in os.scandir(f"{CWD}/logs/{team_name}") if file.is_dir() and trial_name in file.path and "best" not in file.path.split("/")[-1]]
                    most_recent_trial_num = sorted([int(trial.split("_")[-1]) for trial in trials_run])[-1]
                    while not os.path.exists(f"{CWD}/logs/{team_name}/{trial_name}_{most_recent_trial_num}/trial_log.txt"):
                        sleep(1)
                    with open(f"{CWD}/logs/{team_name}/{trial_name}_{most_recent_trial_num}/trial_log.txt",'r') as file:
                        num_lines = len(file.readlines())
                    if num_lines==1:
                        print("Trial did not run correctly. Trying again")
                        os.system(f"rm -rf {CWD}/logs/{team_name}/{trial_name}_{most_recent_trial_num}")
                    else:
                        run_correctly = True
                    os.system(f"docker stop {team_name}")
                num_trials_run+=1
                if trial_count >= MAX_ITERATIONS_PER_TRIAL:
                    continue
        print("="*50)
        print("Completed all trials for team: "+team_name)
        print("="*50)