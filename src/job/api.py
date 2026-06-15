import typer
from functools import wraps

api_app = typer.Typer(help = "Machine-readable JSON API for programmatic use.")

def out(output: dict | Exception):
    import json
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
    from job import workbench as wb
    from job import pbsqueue as q

    current = wb.workbench_current()
    if current is None:
        out([])
        return
    current = current[0]
    job_id = wb.get_job_id(current)
    if job_id is None:
        out([])
        return
        
    out([q.info(job_id)])


    

@api_app.command()
@handle_errors
def start(profile: str = "default"): 
    """Start a new PBS workbench"""
    from job import workbench as wb

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
    from job import workbench as wb
    current = wb.workbench_current()
    if current is None:
        out([])
        return 
    
    wb.workbench_stop(current[0])
    out([])
   
@api_app.command()
@handle_errors
def list_profiles():
    """Get existing profiles"""
    from job import workbench as wb

    out(wb.profile_list())