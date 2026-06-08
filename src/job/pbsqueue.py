import subprocess
import os
import json

from job import format
from job import places as ps

def exists(job_id: str="default") -> bool:
    code = subprocess.run(["qstat", "-f", job_id], stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)
    return code.returncode == 0


def delete(job_id: str) -> bool: 
    code = subprocess.run(["qdel", job_id], text=True)

    return code.returncode == 0


def submit(script: str) -> str:
    script = os.path.normpath(script)
    if not os.path.exists(script):
        raise FileNotFoundError(f"Script {script} not found")
    
    job_id = subprocess.check_output(["qsub", script], text=True).rstrip()

    return job_id



def info(job_id: str):
    try:
        job_info = subprocess.check_output(["qstat", "-F", "json", "-f", job_id], text=True)
    except subprocess.CalledProcessError as e:
        if e.returncode == 153:
            raise RuntimeError(f"Job id {job_id} does not appear to be running")
        else:
            e

    job_info = json.loads(job_info)
    job_info = job_info["Jobs"][job_id]

    requested = dict(
                walltime = format.walltime_to_secs(job_info["Resource_List"]["walltime"]),
                memory = format.standardise_mem(job_info["Resource_List"]["mem"]),
                ncpus = job_info["Resource_List"]["ncpus"],
            )
    used = dict(
            walltime = 0,
            memory = 0,
            cpu = 0,
        )
    if "resources_used" in job_info:
        used = dict(
                    walltime = format.walltime_to_secs(job_info["resources_used"].get("walltime", "00:00:00")),
                    memory = format.standardise_mem(job_info["resources_used"].get("mem", "0b")),
                    cpu = job_info["resources_used"].get("cpupercent", 0) / job_info["resources_used"].get("ncpus", requested["ncpus"]),
                )
   
    job_info = dict(
        requested = requested,
        used = used,
        queue = job_info["queue"],
        state = job_info["job_state"],
        jobdir = job_info.get("jobdir", ps.home()),
        # This gets only the first one listed for multi-node jobs,
        # but that's ok because that's the primary usage. 
        hostname = job_info.get("exec_host", "").split("/")[0],
        comment = job_info.get("comment", ""),
        job_id = job_id,
    )

    # This doesn't work realiably, so for now let's just use 
    # the reported memory usage. 
    # mem = get_used_memory(job_info["hostname"])
    # if mem is not None:
    #     job_info["used"]["memory"] = mem

    su = su_compute(queue = job_info["queue"], 
                    walltime = job_info["requested"]["walltime"], 
                    ncpus =  job_info["requested"]["ncpus"], 
                    memory =  job_info["requested"]["memory"]
                    )

    job_info["su"] = su

    return job_info


def get_used_memory(hostname: str) -> int:
    if hostname == "":
        return 0

    result = subprocess.run(
        [
            "ssh",
            hostname,
            r"ps aux | grep $USER | grep -v grep | awk '{sum+=$6} END {print sum*1024}'",
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return None
    try:
        return int(result.stdout.strip())
    except ValueError:
        return None




QUEUE_RATES: dict[str, float] = {
    "normal": 2,
    "express": 6,
    "hugemem": 3,
    "megamem": 5,
    "gpuvolta": 3,
    "normalbw": 1.25,
    "expressbw": 3.75,
    "hugemembw": 1.25,
    "megamembw": 1.25,
    "copyq": 2,
}

QUEUE_RAM_PER_CPU: dict[str, float] = {
    "normal": 4,
    "express": 4,
    "hugemem": 31,
    "megamem": 62,
    "gpuvolta": 8,
    "normalbw": 9,
    "expressbw": 9,
    "hugemembw": 37,
    "megamembw": 47,
    "copyq": 2,
}

def su_compute(queue: str, walltime: int, ncpus: int, memory: int) -> int:
    queue = queue.removesuffix("-exec")
    walltime_hours = walltime / 3600

    ram_per_cpu = QUEUE_RAM_PER_CPU[queue]
    mem_su = memory / 1024**3 / ram_per_cpu

    su = QUEUE_RATES[queue] * max(mem_su, ncpus) * walltime_hours
    return su

def su_advice(queue: str, ncpus: int, memory: int) -> str:
    queue = queue.removesuffix("-exec")
    ram_per_cpu = QUEUE_RAM_PER_CPU[queue]
    mem_su = memory / 1024**3 / ram_per_cpu

    if mem_su == ncpus:
        advice = "Optimal memory and CPU request."
    elif mem_su < ncpus:
        ceiling, unit_ceiling = ncpus * ram_per_cpu, "GB RAM"
        floor, unit_floor = round(mem_su), "CPUs"
    else:
        ceiling, unit_ceiling = round(mem_su), "CPUs"
        floor, unit_floor = round(ncpus * ram_per_cpu), "GB RAM"
    
    advice = f"Can increase {unit_ceiling} to {ceiling} or reduce {unit_floor} to {floor}."

    return advice
