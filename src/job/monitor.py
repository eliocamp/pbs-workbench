import os
import urwid as uw

from job import pbsqueue as q
from job import format

palette = [
    ('complete', 'default', 'white'),
    ('normal', 'white', 'default'),
]

def ProgressTable(rows_data):
    """
    Build a centred progress bar table.

    Args:
        rows_data: list of (label, bar, suffix) tuples where label and suffix
                   are uw.Text widgets and bar is a uw.ProgressBar widget.

    Returns:
        A uw.Padding widget containing a uw.Pile of uw.Columns rows,
        centred at 80% of terminal width.
    """
    LABEL_WIDTH = max(len(r[0].text) for r in rows_data)
    SUFFIX_WIDTH = max(len(r[2].text) for r in rows_data)

    rows = []
    for label, bar, suffix in rows_data:
        rows.append(uw.Columns([
            ('fixed', LABEL_WIDTH, label),
            bar,
            ('fixed', SUFFIX_WIDTH, suffix),
        ]))

    return uw.Padding(uw.Pile(rows), align='center', width=('relative', 80))

class ProgressBarLabel(uw.ProgressBar):
    def __init__(self, normal, complete, current, done, label = ""):
        super().__init__(normal, complete, current, done)
        self.label = label
    def get_text(self):
        text = super().get_text()
        return self.label + " " + text 


STATUS_FRAMES = [' ', '▂', '▃', '▄', '▅', '▆','▇', '█']
TITLE = "PBS Workbench Monitor"
status_widget = uw.Text(f"{TITLE} {STATUS_FRAMES[0]}", align="center")

def start_fill(loop, seconds = 10):
    steps = len(STATUS_FRAMES)
    interval = seconds / steps

    def tick(loop, step):
        status_widget.set_text(f"{TITLE} {STATUS_FRAMES[step]}")
        if step < steps - 1:
            loop.set_alarm_in(interval, tick, step + 1)

    status_widget.set_text(f"{TITLE} {STATUS_FRAMES[0]}")
    loop.set_alarm_in(interval, tick, 1)

def build_ui(info):    
    used_secs = info["used"]["walltime"]
    req_secs = info["requested"]["walltime"]
    cpu_pct = info["used"]["cpu"]
    job_id = info["job_id"]
    su = info["su"]
    used_su = su * used_secs / req_secs

    user = os.environ["USER"]
    wd = os.getcwd()

    div = uw.Divider("─")
    
    header = [div, status_widget, div]

    body = []

    title = [uw.Text(f"Job ID: {job_id}"), uw.Text(f"Usage: {round(used_su)} SU")]
    body.extend(title)

    job_status = info["state"]
    hostname = info["hostname"]

    if job_status == "R":
        status = [uw.Text(f"Running on node {hostname}")]
    elif job_status == "Q":
        status = [uw.Text("Waiting for job to run.")]
    elif job_status == "H":
        status = [uw.Text("Job is on hold")]
    else:
        status = [uw.Text("Unknown status")]

    if job_status != "R":
        status.append(uw.Text(info["comment"]))

    body.extend(status)

    if job_status == "R": 
        ssh = map(uw.Text,
            [
                "",
                "SSH command: ",
                f"   ssh -X {user}@{hostname}",
                "SSH tunnel: ",
                f"   ssh -L 8080:127.0.0.1:8080 {user}@{hostname}",
                "Remote-ssh:",
                f"   --remote ssh-remote+{hostname} {wd}",
                ""
            ]
        )
        body.extend(ssh)

        used_mem_gb = round(info["used"]["memory"] / 1024**3, 1)
        req_mem_gb = round(info["requested"]["memory"] / 1024**3, 1)
        memory_pre = uw.Text(f"{used_mem_gb}GB ", align = "right")
        memory_bar = ProgressBarLabel("normal", "complete", current = used_mem_gb, done = req_mem_gb, label = "Memory:")
        memory_after = uw.Text(f" {req_mem_gb}GB", align = "left")

        memory_row = (memory_pre, memory_bar, memory_after)
        
 
        walltime_pre = uw.Text(format.secs_to_walltime(used_secs) + " ", align = "right")
        walltime_bar = ProgressBarLabel("normal", "complete", used_secs, req_secs, label = "Progress:")
        walltime_after = uw.Text(" " + format.secs_to_walltime(req_secs - used_secs), align = "left")

        walltime_row = (walltime_pre, walltime_bar, walltime_after)
        
        cpu_row = (uw.Text(" "),
        ProgressBarLabel("normal", "complete", int(cpu_pct), 100, label = "CPU:"),
        uw.Text(" ")
        )

        body.append(ProgressTable([walltime_row, memory_row, cpu_row]))
    
    body = uw.Padding(uw.Pile(body), left = 1, right = 1)

    footer = [div]

    ui = []
    ui.extend(header)
    ui.append(body)
    ui.extend(footer)
    
    ui = uw.Pile(ui)
    
    main = uw.Filler(ui, "top")

    return main

def monitor(job_id: str):
    def UI(loop = None, data = None):
        info = q.info(job_id)
        ui = build_ui(info)

        if loop is None:
            loop = uw.MainLoop(ui, palette = palette, handle_mouse = False)
            start_fill(loop)
            loop.set_alarm_in(10, UI)
            loop.run()
        else:
            loop.widget = ui
            loop.set_alarm_in(10, UI)
            start_fill(loop)
            return loop
    
    UI()


