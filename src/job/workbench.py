import json
import os
import tempfile
from importlib.resources import files
import subprocess

from job import places as ps
from job import pbsqueue as q

DIRECTIVE_ARGUMENTS = dict(project = "P", queue = "q", name = "N", resources = "l")

def as_list(value):
    if not isinstance(value, list):
        value = [value]
    return value

def join_values(value):
    return "+".join(map(str, as_list(value)))

def parse_value(value):
    if isinstance(value, str):
        return [value]

    return [f"{key}={join_values(value)}" for key, value in value.items()]
    
def parse_directive(key, value):
    argument = DIRECTIVE_ARGUMENTS[key]

    value = parse_value(value)

    directive = [f"#PBS -{argument} {value}" for value in value]
    return directive

def flatten(xs):
    out = []
    for x in xs:
        if isinstance(x, list):
            out.extend(flatten(x))
        else:
            out.append(x)
    return out

def jobscript_from_json(json_file: str, workbench_file: str) -> str:
    with open(json_file, "r") as f:
        config = json.load(f)

    directives = [parse_directive(key, value) for key, value in config.items()]
    directives = flatten(directives)
  
    defaults = ["#PBS -l wd", f"#PBS -o {ps.logs_folder()}", f"#PBS -e {ps.logs_folder()}"]

    directives.extend(defaults)

    idle_file = files("job.data") / "idle.sh"

    with open(idle_file) as f:
        idle = [line.rstrip() for line in f]

    fd, path = tempfile.mkstemp()

    with os.fdopen(fd, "w") as f:
        f.write("#!/bin/bash\n")
        f.writelines(line + "\n" for line in directives)
        f.write(f'WORKBENCH_FILE="{workbench_file}"')
        f.writelines(line + "\n" for line in idle)

    return path

# There could be a race condition between checking for free files 
# and creating the file, so we need to wrap this in a try-loop. 
def _try_workbench_file_new() -> str:
    dir = ps.workbench_dir()
    os.makedirs(dir, exist_ok = True)

    current = os.listdir(dir)
    if len(current) == 0:
        file_number = 0
    else:
        current = set(map(int, current))
        file_number = next(i for i in range(len(current) + 1) if i not in current)

    file = str(file_number).zfill(2)
    path = f"{dir}/{file}"
    with open(path, "x"):
        pass
    return path

def workbench_file_new() -> str:
    while True:
        try: 
            return _try_workbench_file_new()
        except FileExistsError:
            continue



def get_profile(profile: str, format: str = "json") -> str | None:
    profile_json = f"{ps.profile_folder()}/{profile}.{format}"
    if not os.path.exists(profile_json):
        return None
    return profile_json 

def profile_list() -> list[str]:
    profiles = os.listdir(ps.profile_folder())
    if len(profiles) == 0:
        return []
    return [p.rsplit(".", 1)[0] for p in profiles if p.endswith("json")]

def workbench_start(profile: str) -> str:
    job_json = get_profile(profile)

    if job_json is None:
        raise FileNotFoundError(f"Profile {profile} not found.")
    
    workbench_file = workbench_file_new()
    job_script = jobscript_from_json(job_json, workbench_file)

    os.makedirs(ps.logs_folder(), exist_ok = True)

    job_id = q.submit(job_script)
    with open(workbench_file, "w") as f:
        f.writelines(job_id)

    return workbench_file

def workbench_files() -> list[str]:
    dir = ps.workbench_dir()
    os.makedirs(dir, exist_ok = True)

    files = [f"{dir}/{f}" for f in os.listdir(dir)]

    return files

def get_job_id(workbench_file: str) -> str:
    try:
        with open(workbench_file, "r") as f:
            job_id = f.readline()
    except FileNotFoundError:
        return None
    
    return job_id


# This could, in theory, run into a race condition if this runs
# exactly between when workbench_start() secures a new workbench file
# and before it writes the job_id into it, but that's unlikely. 
# A possible fix coudl be to use a .LOCK file to signal that the
# job is being submitted. 
def workbench_is_running(file: str) -> bool:
    job_id = get_job_id(file)
    return job_id is not None and job_id != "" and q.exists(job_id)

# In principle, jobs should clean after themselves, but a job 
# could be killed before starting, and then the workbench file 
# would be kept dangling 
def workbench_files_clean() -> int:
    files = workbench_files()
    if len(files) == 0:
        return 0
    
    to_remove = [file for file in files if not workbench_is_running(file)]
    if len(to_remove) == 0:
        return 0
    
    for file in to_remove:
        try:
            os.remove(file)
        except FileNotFoundError:
            continue

    return len(to_remove)


def workbench_list() -> list[str]:
    proj_files = workbench_files()
    proj_files = [file for file in proj_files if workbench_is_running(file)]
    return proj_files

def workbench_current() -> str:
    proj_files = workbench_list()
    if len(proj_files) == 0:
        return None

    return proj_files

def workbench_stop(workbench_file: str) -> bool:
    if workbench_is_running(workbench_file):
        with open(workbench_file, "r") as f:
            job_id = f.readline()
        q.delete(job_id)
    
    # The workbench self-cleanup might have gotten the file first. 
    try: 
        os.remove(workbench_file)
    except FileNotFoundError: 
        pass

    return job_id
    
def ssh_run(command: str, job_id: str) -> int:
    info = q.info(job_id)
    
    ssh = f"{os.environ["USER"]}@{info["hostname"]}"
    
    return subprocess.run(["ssh", ssh, command])


def run_jupyter(job_id: str):
    fd, path = tempfile.mkstemp() 
    os.close(fd)
    jupyter = f"module load jupyterlab && nohup jupyter lab --no-browser --port=8080 < /dev/null > {path} 2>&1 & disown"

    ssh_run(jupyter, job_id)


def parse_old_profile(old_file: str) -> str:
    """
    Reads from the old profile design (.sh files with PBS directives)
    to the new one (directives as fields in json file)
    """

    try:
        with open(old_file, "r") as f:
            lines = f.readlines()
    except Exception as e:
        raise e

    lines = [line.replace("#PBS -", "").strip() for line in lines if line.startswith("#PBS")]

    directives = dict()
    directives["resources"] = dict()
    directive_inverse = {v: k for k, v in DIRECTIVE_ARGUMENTS.items()}

    line = lines[0]
    for line in lines:
        directive_type, directive_value = line.split(" ", 2)
        directive_type = directive_inverse.get(directive_type, None)

        if directive_type is None:
            continue
        if directive_type == "resources":
            split = directive_value.split("=", 2)
            
            # This skips "l wd" 
            if len(split) != 2:
                continue

            value_type, directive_value = split
            
            if value_type == "storage":
                directive_value = directive_value.split("+")
            directives[directive_type][value_type] = directive_value
        else :
            directives[directive_type]  = directive_value
        
    return directives
 