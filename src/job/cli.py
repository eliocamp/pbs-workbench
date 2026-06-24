import os

os.environ["TYPER_USE_RICH"] = "0"
import typer
from click.shell_completion import CompletionItem

from job.api import api_app

app = typer.Typer()

app.add_typer(api_app, name="api")


def version_callback(value: bool):
    if value:
        from importlib.metadata import version

        print(version("job"))
        raise typer.Exit()


# sys.tracebacklimit = 0
@app.callback(invoke_without_command = True)
def job(
    ctx: typer.Context,
    version: bool = typer.Option(
        None,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
):
    """PBS Workbench - Interactive PBS Job Management

    \b
    Examples:
      job start            Start with default profile
      job start myprofile  Start with a specific profile
      job monitor          Monitor the running workbench
    """
    if ctx.invoked_subcommand is None:
        print(ctx.get_help())


def complete_profiles(ctx, param, incomplete):
    from job import places as pl

    profiles_dir = pl.profile_folder()
    profiles = os.listdir(profiles_dir)

    return [
        CompletionItem(p.rsplit(".", 1)[0])
        for p in profiles
        if p.startswith(incomplete)
    ]


@app.command()
def start(profile: str = typer.Argument("default", shell_complete=complete_profiles)):
    """Start a new PBS workbench"""
    from job import workbench as wb
    from job import monitor as mon

    current = wb.workbench_current()
    if current is not None:
        print("Workbench already running")
        return
    workbench_file = wb.workbench_start(profile)
    mon.monitor(workbench_file)


@app.command()
def monitor():
    """Monitor the current running workbench"""
    from job import workbench as wb
    from job import monitor as mon

    current = wb.workbench_current()
    if current is None:
        print("No workbench runnning.")
        return

    current = current[0]

    mon.monitor(current)


@app.command()
def list():
    """List running workbenchs"""
    from job import workbench as wb

    running = [os.path.basename(file) for file in wb.workbench_list()]
    print("\n".join(running))


@app.command()
def end():
    """Stop the current running workbench"""
    from job import workbench as wb

    current = wb.workbench_current()
    if current is None:
        print("No workbench runnning.")
        wb.workbench_files_clean()
        return

    current = current[0]
    try:
        wb.workbench_stop(current)
    except RuntimeError as e:
        print(e)
    wb.workbench_files_clean()


@app.command()
def profile(profile: str = typer.Argument("default", shell_complete=complete_profiles)):
    """Create or modify a job profile interactively"""
    import json
    from job import workbench as wb
    from job import profile_editor

    profile_file = wb.get_profile(profile)
    if profile_file is None:
        profile_file = wb.get_profile(profile, format="sh")
        if profile_file is not None:
            config = wb.parse_old_profile(profile_file)
        else:
            config = profile_editor.DEFAULT_CONFIG

        config["name"] = profile
    else:
        with open(profile_file, "r") as f:
            config = json.load(f, parse_int=lambda x: str(x))
    profile_editor.ProfileEditor(config).run()


if __name__ == "__main__":
    app()
