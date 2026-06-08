import typer
import json 
from functools import wraps

from job import workbench as wb
from job import pbsqueue as q

api_app = typer.Typer(help = "Machine-readable JSON API for programmatic use.")



def out(output: dict | Exception):
    if isinstance(output, Exception):
        print(json.dumps(dict(error = str(output), output = [])))
    else:
        print(json.dumps(dict(output = output)))

def handle_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            out(e)
    return wrapper

@api_app.command()
@handle_errors
def info():
    """Get info on current workbench"""
    current = wb.workbench_current()
    if current is None:
        out([])
        return
    job_id = wb.get_job_id(current)
    out([q.info(job_id)])


    

@api_app.command()
@handle_errors
def start(profile: str = "default"): 
    """Start a new PBS workbench"""
    current = wb.workbench_current()
    if current is not None:
        raise Exception("Workbench already running")
        return 
    workbench_file = wb.workbench_start(profile)
    job_id = wb.get_job_id(workbench_file)
    out(dict(workbench_file = workbench_file, job_id = job_id))
    

@api_app.command()
@handle_errors
def end():
    """Stop the current running workbench"""
    wb.workbench_stop()
    out({})
   
@api_app.command()
@handle_errors
def list_profiles():
    """Get existing profiles"""
    out(wb.profile_list())