import os
import sys
import time
import json
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from git import Repo

CONFIG_FILE = "git_auto_sync_config.json"

class GitAutoSync:
    def __init__(self, master):
        self.master = master
        master.title("Git Auto Sync")

        self.repo_list = self.load_config()
        self.status_vars = {}
        self.last_sync_vars = {}

        self.repo_frame = ttk.Frame(master)
        self.repo_frame.pack(padx=10, pady=10)

        self.create_menu()
        self.create_repo_frames()

        self.sync_thread = None
        self.start_sync_thread()

    def create_menu(self):
        menubar = tk.Menu(self.master)
        self.master.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Add Repository", command=self.add_repo)
        file_menu.add_command(label="Remove Repository", command=self.remove_repo)
        menubar.add_cascade(label="File", menu=file_menu)

    def create_repo_frames(self):
        for repo_path in self.repo_list:
            repo_name = os.path.basename(repo_path)

            status_var = tk.StringVar()
            last_sync_var = tk.StringVar()

            repo_frame = ttk.Frame(self.repo_frame)
            repo_frame.pack(anchor="w", padx=10, pady=5)

            ttk.Label(repo_frame, text=repo_name).pack(side="left")
            ttk.Label(repo_frame, textvariable=status_var).pack(side="left", padx=10)
            ttk.Label(repo_frame, textvariable=last_sync_var).pack(side="left")

            self.status_vars[repo_path] = status_var
            self.last_sync_vars[repo_path] = last_sync_var

    def add_repo(self):
        repo_path = filedialog.askdirectory(title="Select Repository Folder")
        if repo_path and repo_path not in self.repo_list:
            self.repo_list.append(repo_path)
            self.save_config()
            self.create_repo_frames()
            self.start_sync_thread()

    def remove_repo(self):
        repo_path = filedialog.askdirectory(title="Select Repository Folder to Remove")
        if repo_path and repo_path in self.repo_list:
            self.repo_list.remove(repo_path)
            self.save_config()
            self.repo_frame.destroy()
            self.repo_frame = ttk.Frame(self.master)
            self.repo_frame.pack(padx=10, pady=10)
            self.create_repo_frames()

    def start_sync_thread(self):
        if not self.sync_thread or not self.sync_thread.is_alive():
            self.sync_thread = threading.Thread(target=self.sync_repos)
            self.sync_thread.start()

    def sync_repos(self):
        while True:
            for repo_path in self.repo_list:
                try:
                    repo = Repo(repo_path)
                    repo.git.pull()

                    untracked_files = []
                    for item in repo.untracked_files:
                        if item[0].isalnum():
                            untracked_files.append(item)

                    if untracked_files:
                        repo.git.add(untracked_files)

                    if repo.is_dirty():
                        repo.git.add(update=True)
                        repo.git.commit("-m", "Auto commit")
                        repo.git.push()

                    self.status_vars[repo_path].set("Synced")
                    self.last_sync_vars[repo_path].set(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                except Exception as e:
                    self.status_vars[repo_path].set("Error: " + str(e))

            time.sleep(60)  # Sync every 60 seconds

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        return []

    def save_config(self):
        with open(CONFIG_FILE, "w") as f:
            json.dump(self.repo_list, f)

def run_app():
    root = tk.Tk()
    app = GitAutoSync(root)
    root.mainloop()

if __name__ == "__main__":
    if getattr(sys, 'frozen', False):
        # Running as a bundled executable
        run_app()
    else:
        # Running as a script
        if not subprocess.call(["pip", "install", "gitpython"]):
            run_app()
        else:
            messagebox.showerror("Error", "Failed to install required dependencies.")
