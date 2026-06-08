import os 

def home() -> str:
    return os.environ["HOME"]
    
def workbench_home():
    return f"{home()}/pbs-workbench"

def workbench_dir() -> str:
    return f"{workbench_home()}/workbenches/"
    

def workbench_file() -> list[str]:
    return f"{workbench_dir()}/00"


def profile_folder():
    return f"{workbench_home()}/profiles"

def logs_folder():
    return f"{workbench_home()}/logs"
