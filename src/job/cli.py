import typer
from click.shell_completion import CompletionItem

from job.api import api_app

app = typer.Typer()

app.add_typer(api_app, name="api")

# sys.tracebacklimit = 0
@app.callback(invoke_without_command=True)
def job(ctx: typer.Context):
    """PBS Workbench - Interactive PBS Job Management
    
    \b
    Examples:
      job start            Start with default profile
      job start myprofile  Start with a specific profile
      job monitor          Monitor the running job
    """
    if ctx.invoked_subcommand is None:
        print(ctx.get_help())

def complete_profiles(ctx, param, incomplete):
    from job import places as pl
    import os
    profiles_dir = pl.profile_folder()
    profiles = os.listdir(profiles_dir)
    
    return [
        CompletionItem(p.rsplit(".", 1)[0]) for p in profiles
        if p.startswith(incomplete)
    ]

@app.command()
def start(profile: str = typer.Argument("default", shell_complete = complete_profiles)): 
    """Start a new PBS workbench"""
    from job import workbench as wb
    from job import monitor as mon

    current = wb.workbench_current()
    if current is not None:
        print("Workbench already running")
        return 
    workbench_file = wb.workbench_start(profile)
    job_id = wb.get_job_id(workbench_file)
    mon.monitor(job_id)

@app.command()
def monitor():
    """Monitor the current running workbench"""
    from job import workbench as wb
    from job import monitor as mon

    current = wb.workbench_current()
    if current is None:
        print("No workbench runnning.")
        return 

    job_id = wb.get_job_id(current)
    if job_id is None:
        print("No workbench runnning.")
        return 
    mon.monitor(job_id)


@app.command()
def list():
    """List running workbenchs"""
    from job import workbench as wb
    import os
    running = [os.path.basename(file) for file in wb.workbench_list()]
    print("\n".join(running))
    


@app.command()
def end():
    """Stop the current running workbench"""
    from job import workbench as wb

    try:
        wb.workbench_stop()
    except RuntimeError as e:
        print(e)


@app.command()
def profile(profile: str = typer.Argument("default", shell_complete = complete_profiles)):
    """Create or modify a job profile interactively"""
    import json
    from job import workbench as wb
    from job import profile_editor

    profile_file = wb.get_profile(profile)
    if profile_file is None:
        config = profile_editor.DEFAULT_CONFIG
        config["name"] = profile
    else:
        with open(profile_file, "r") as f:
            config = json.load(f)
    profile_editor.ProfileEditor(config).run()

    

if __name__ == "__main__":
    app()
