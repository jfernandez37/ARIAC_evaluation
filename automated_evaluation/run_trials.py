import os
from copy import copy
import customtkinter as ctk
from tkinter import *
from functools import partial
import subprocess
from time import sleep
import docker
import docker.models
from docker.models.containers import Container as DockerContainer
from typing import Optional
import shutil


class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"

def trial_succeeded(trial_log: str) -> bool:   
    if os.path.exists(trial_log):
        with open(trial_log, "r") as file:
            if len(file.readlines()) > 1:
                return True
            else:
                return False
    
    print(bcolors.FAIL+"Unable to find most log file for most recent run"+bcolors.ENDC)
    return False

def get_most_recent_trial_log(team_name: str, trial_name: str) -> str:
    most_recent_trial_folder = get_most_recent_trial_folder(team_name, trial_name)
    
    trial_log = os.path.join(most_recent_trial_folder, "trial_log.txt")
    
    return trial_log

def get_most_recent_trial_folder(team_name: str, trial_name: str):
    folders = [file.path for file in os.scandir(os.path.join(os.getcwd(), "logs", team_name))]
    
    trial_folders = filter(lambda x: trial_name in x, folders)
    
    return sorted(trial_folders, key=lambda x: int(x.split("_")[-1]))[-1]

def delete_most_recent_trial_folder(team_name: str, trial_name: str):
    os.system(f"rm -rf {get_most_recent_trial_folder(team_name, trial_name)}")

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

        self.team_names = sorted([file.replace(".yaml","") for file in os.listdir(os.getcwd()+"/competitor_configs") if ".yaml" in file])
        self.trial_names = sorted([file.replace(".yaml","") for file in os.listdir(os.getcwd()+"/trials") if ".yaml" in file])
            
        self.left_column, self.middle_column, self.right_column = 1,2,3
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(100, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(4, weight=1)

        self.team_vars = [ctk.StringVar() for _ in range(len(self.team_names))]
        self.trial_vars = [ctk.StringVar() for _ in range(len(self.trial_names))]
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
            cb = ctk.CTkCheckBox(self, text=self.team_names[i], variable=self.team_vars[i], onvalue="1", offvalue="0", height=1, width=20)
            cb.grid(column = self.left_column, row = i+1, sticky=NW, padx = 25)
        select_all_teams_button = ctk.CTkButton(self, text="Select all teams", command=partial(self.select_all, self.team_vars))
        select_all_teams_button.grid(column = self.left_column, row = len(self.team_vars)+1)

        for i in range(len(self.trial_vars)):
            cb = ctk.CTkCheckBox(self, text=self.trial_names[i], variable=self.trial_vars[i], onvalue="1", offvalue="0", height=1, width=20)
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
        temp_team_selections = [self.team_names[i] for i in range(len(self.team_names)) if self.team_vars[i].get()=="1"]
        self.team_selections = [name for name in self.team_names if name in temp_team_selections]
        temp_trials_selected = [self.trial_names[i] for i in range(len(self.trial_names)) if self.trial_vars[i].get()=="1"]
        self.trial_selections = [name for name in self.trial_names if name in temp_trials_selected]
        self.num_iter_selection = self.num_iter_var.get()
        self.max_iter_selection = self.max_iter_var.get()
        self.use_nvidia = self.use_nvidia_var.get()=="1"
        self.rebuild_containers = self.rebuild_containers_var.get()=="1"
        self.update_trials = self.update_trials_var.get()=="1"
        self.destroy()

if __name__ == "__main__":
    # print(bcolors.OKCYAN + "ARIAC logs for this trial can be found at:" + bcolors.ENDC)
    # Get options from GUI
    setup_gui = Options_GUI()
    setup_gui.mainloop()

    if 0 in [len(setup_gui.team_selections),len(setup_gui.trial_selections), setup_gui.num_iter_selection]:
        print("Exited out of GUI. Not running any trials.")
        quit()
    else:
        team_names = setup_gui.team_selections
        trial_names = setup_gui.trial_selections
        num_iter_per_trial = setup_gui.num_iter_selection
        max_iter_per_trial = setup_gui.max_iter_selection
        use_nvidia = setup_gui.use_nvidia
        rebuild_containers = setup_gui.rebuild_containers
        update_trials = (setup_gui.update_trials if not rebuild_containers else False)
    
    # Move existing log files
    if os.path.exists(os.path.join(os.getcwd(), "logs")) and len(os.listdir(os.path.join(os.getcwd(),"logs")))>0:
        num = 1
        if not os.path.exists(os.path.join(os.getcwd(),"old_logs")):
            os.mkdir(os.path.join(os.getcwd(),"old_logs"))
            os.mkdir(os.path.join(os.getcwd(),"old_logs", "competition_run_1"))
        else:
            used_nums = []
            for folder in os.listdir(os.path.join(os.getcwd(),"old_logs")):
                if "competition_run_" in folder:
                    used_nums.append(int(folder.split("_")[-1]))
            os.mkdir(os.path.join(os.getcwd(),"old_logs", f"competition_run_{max(used_nums)+1}"))
            num = max(used_nums)+1
        shutil.move(f"{os.getcwd()}/logs", f"{os.getcwd()}/old_logs/competition_run_{num}")    
        
    # Build/Rebuild all containers
    docker_client = docker.DockerClient()
    all_containers: list[DockerContainer] = docker_client.containers.list(all=True)
    
    team_containers: dict[str, Optional[DockerContainer]]  = {team : None for team in team_names}
    for team in team_names:
        for container in all_containers:
            if container.name == team:
                team_containers[team] = container
                break
            
    if rebuild_containers:
        for team in team_names:
            # Remove existing containers
            if team_containers[team] is not None and team.lower() != "sirius":
                container.remove(force=True)
            
            # Build new container
            build_command = ["./build_container.sh", team,]
            if use_nvidia:
                build_command.append("nvidia")
            process = subprocess.run(build_command)
            
            all_containers = docker_client.containers.list(all=True)
            
            try:
                team_containers[team] = [c for c in all_containers if c.name == team][0]
            except IndexError:
                team_containers[team] = None
                print(bcolors.FAIL+"Unable to rebuild container for team", team+bcolors.ENDC)
            
    # Update trials
    if update_trials:
        for team in team_names:
            if not team_containers[team] is None:
                process = subprocess.run(["./update_trials.sh",team])

    # Stop all containers
    for container in team_containers.values():
        print(bcolors.OKGREEN+"Stopping container",container.name,bcolors.ENDC)
        container.stop()
    
    # Run trials
    for team_name, container in team_containers.items():
        for trial_name in trial_names:
            trial_runs = 0
            completed_runs = 0
            
            while completed_runs < num_iter_per_trial:
                print(bcolors.OKGREEN+"Restarting container",team_name,container.name,bcolors.ENDC)
                container.restart()
                
                # Start trial
                print(bcolors.OKGREEN+f"On trial {trial_runs} of {max_iter_per_trial} for "+container.name,bcolors.ENDC)
                print(bcolors.OKGREEN+f"Completed runs: {completed_runs} out of {num_iter_per_trial} for "+container.name,bcolors.ENDC)
                run_command = ["./run_trial.sh", team_name, trial_name]
                p = subprocess.Popen(run_command)
                p.wait()
                
                sleep(2)
                
                most_recent_trial_log = get_most_recent_trial_log(team_name, trial_name)
                if os.path.exists(most_recent_trial_log):
                    if trial_succeeded(most_recent_trial_log):
                        completed_runs+=1
                    else:
                        print(bcolors.FAIL+"Trial did not run correctly. Trying again"+bcolors.ENDC)
                        delete_most_recent_trial_folder(team_name, trial_name)
                else:
                    print(bcolors.FAIL+"Unable to find log file. Running again"+container.name,bcolors.ENDC)
                    delete_most_recent_trial_folder(team_name, trial_name)
                
                trial_runs+=1
                
                if trial_runs >= max_iter_per_trial:
                    break
        
        container.stop()
                
        print(bcolors.OKCYAN+"="*50)
        print("Completed all trials for team: "+team_name)
        print("="*50+bcolors.ENDC)