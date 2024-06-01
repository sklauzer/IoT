import os
import subprocess

def set_working_dir():
    current_dir = os.getcwd()
    git_root = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], cwd=current_dir)
    git_root = git_root.decode("utf-8").strip()
    os.chdir(git_root)
    new_dir = os.getcwd()
    return new_dir