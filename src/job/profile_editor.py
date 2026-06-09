import json
import urwid as uw
import os

from job import places as ps


PALETTE = [
    ("label", "light gray", "default"),
]
PROJECT = os.environ["PROJECT"]

QUEUES = ["normal", "normalbw", "bigmem", "bigmembw"]

DEFAULT_CONFIG = {
    "queue": QUEUES[0],
    "name": "default",
    "project": PROJECT,
    "resources": {
        "ncpus": "8",
        "mem": "32GB",
        "walltime": "8:00:00",
        "jobfs": "200GB",
        "storage": [f"scratch/{PROJECT}", f"gdata/{PROJECT}"],
    },
}

def WithLabel(label, widget):
    return (uw.Text(("label", label + " ")), widget)


def Table(rows_data):
    """
    Build a centred progress bar table.

    Args:
        rows_data: list of (uw.Text(), widget) tuples

    Returns:
        A uw.Padding widget containing a uw.Pile of uw.Columns rows
    """
    LABEL_WIDTH = max(len(r[0].text) for r in rows_data)

    rows = []
    for label, widget in rows_data:
        rows.append(
            uw.Columns(
                [
                    ("fixed", LABEL_WIDTH, label),
                    widget,
                ]
            )
        )

    return uw.Padding(uw.Pile(rows), align="right", left=1)


class RadioButtonEnter(uw.RadioButton):
    def keypress(self, size, key):
        if key == "enter":
            return "down"
        return super().keypress(size, key)


class RadioButtonGroup:
    def __init__(self, options, default=None):
        group = []
        if default is None:
            default = options[0]

        for option in options:
            RadioButtonEnter(group, option, state=(option == default))

        self.group = group
        self.default = default

    def __iter__(self):
        for button in self.group:
            yield button

    def get_value(self):
        for rb in self.group:
            if rb.state:
                return rb.label

        return self.default


class EditEnter(uw.Edit):
    def keypress(self, size, key):
        if key == "enter":
            self.edit_pos = 0
            return "down"
        if key == "down":
            self.edit_pos = 0
        if key == "up":
            self.edit_pos = 0
        return super().keypress(size, key)


class TabbedPile(uw.Pile):
    def keypress(self, size, key):
        if key == "tab":
            # If we are at the end (buttons) go to the first
            # If we are not, then go to the end.
            if self.focus_position == len(self.contents) - 1:
                self.focus_position = 3  # first one.
            else:
                self.focus_position = (
                    len(self.contents) - 1
                )  # jump to last widget (buttons)
            return

        return super().keypress(size, key)


class ProfileEditor:
    def __init__(self, config: dict):
        self.exit_message = None
        resources = config.get("resources", DEFAULT_CONFIG["resources"])

        self.name = EditEnter("", config.get("name", ""))
        self.project = EditEnter("", config.get("project", DEFAULT_CONFIG["project"]))
        self.ncpus = EditEnter(
            "", resources.get("ncpus", DEFAULT_CONFIG["resources"]["ncpus"])
        )
        self.walltime = EditEnter(
            "", resources.get("walltime", DEFAULT_CONFIG["resources"]["walltime"])
        )
        self.mem = EditEnter(
            "", resources.get("mem", DEFAULT_CONFIG["resources"]["mem"])
        )
        self.jobfs = EditEnter(
            "", resources.get("jobfs", DEFAULT_CONFIG["resources"]["jobfs"])
        )
        self.storage = EditEnter(
            "",
            "+".join(resources.get("storage", DEFAULT_CONFIG["resources"]["storage"])),
        )

        self.queue = RadioButtonGroup(
            options=QUEUES, default=config.get("queue", DEFAULT_CONFIG["queue"])
        )

        queue_column = uw.Columns([("pack", w) for w in self.queue], dividechars=2)

        btn_save = uw.Button("Save")
        btn_quit = uw.Button("Quit")
        uw.connect_signal(btn_save, "click", lambda _: self.save())
        uw.connect_signal(btn_quit, "click", lambda _: self.quit())

        buttons = uw.Padding(
            uw.Columns([("pack", btn_save), ("pack", btn_quit)], dividechars=4), left=2
        )

        div = uw.Divider("─")
        header = [div, uw.Text("PBS Workbench Editor", align="center"), div]

        body = Table(
            [
                WithLabel("Name:", self.name),
                WithLabel("Queue:", queue_column),
                WithLabel("Project:", self.project),
                WithLabel("CPUs:", self.ncpus),
                WithLabel("RAM:", self.mem),
                WithLabel("Walltime:", self.walltime),
                WithLabel("Jobfs:", self.jobfs),
                WithLabel("Storage:", self.storage),
            ]
        )

        ui = []
        ui.extend(header)
        ui.append(body)
        ui.append(div)
        ui.append(buttons)

        self.ui = uw.Filler(TabbedPile(ui), "top")
        self.loop = uw.MainLoop(self.ui, palette=PALETTE)

    def save(self, force=False):
        filename = self.name.get_edit_text() + ".json"
        path = f"{ps.profile_folder()}/{filename}"

        if not force:
            if os.path.exists(path):
                # This might be the most horrible thing I've done in recent memory
                dialogue = uw.LineBox(
                    uw.Filler(
                        uw.Padding(
                            uw.Pile(
                                [
                                    uw.Text(
                                        f"Profile {self.name.get_edit_text()} already exist"
                                    ),
                                    uw.Columns(
                                        [
                                            (
                                                "pack",
                                                uw.Button(
                                                    "Back",
                                                    on_press=lambda _: setattr(
                                                        self.loop, "widget", self.ui
                                                    ),
                                                ),
                                            ),
                                            (
                                                "pack",
                                                uw.Button(
                                                    "Save anyway",
                                                    on_press=lambda _: (
                                                        setattr(
                                                            self.loop, "widget", self.ui
                                                        ),
                                                        self.save(force=True),
                                                    ),
                                                ),
                                            ),
                                        ],
                                        dividechars=2,
                                    ),
                                ]
                            ),
                            align="center",
                        )
                    )
                )
                overlay = uw.Overlay(
                    dialogue,
                    self.ui,
                    align="center",
                    width=("relative", 80),
                    valign="middle",
                    height=10,
                )
                self.loop.widget = overlay
                return

        config = DEFAULT_CONFIG
        config["name"] = self.name.get_edit_text()
        config["project"] = self.project.get_edit_text()
        config["queue"] = self.queue.get_value()
        config["resources"]["ncpus"] = self.ncpus.get_edit_text()
        config["resources"]["mem"] = self.mem.get_edit_text()
        config["resources"]["walltime"] = self.walltime.get_edit_text()
        config["resources"]["jobfs"] = self.jobfs.get_edit_text()
        config["resources"]["storage"] = self.storage.get_edit_text().split("+")

        with open(path, "w") as f:
            f.writelines(json.dumps(config))
        
        self.quit("Profile saved")
        

    def quit(self, message = None):
        self.exit_message = message
        raise uw.ExitMainLoop()
        
    def run(self):
        self.loop.run()
        if self.exit_message:
            print(self.exit_message)
