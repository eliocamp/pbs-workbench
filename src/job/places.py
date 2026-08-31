import os 
from functools import wraps

def ensure_path(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        path = func(*args, **kwargs)
        os.makedirs(path, exist_ok = True)
        return path
    return wrapper

def home() -> str:
    return os.environ["HOME"]

@ensure_path
def workbench_home():
    return f"{home()}/pbs-workbench"

@ensure_path
def workbench_dir() -> str:
    return f"{workbench_home()}/workbenches/"
    
@ensure_path
def workbench_file() -> list[str]:
    return f"{workbench_dir()}/00"

@ensure_path
def profile_folder():
    return f"{workbench_home()}/profiles"

@ensure_path
def logs_folder():
    return f"{workbench_home()}/logs"
