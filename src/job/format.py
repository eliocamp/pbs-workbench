import re

def standardise_mem(mem: str) -> int:
    """
    Standardises mem to bytes.
    """

    value = re.compile(r"\d+").search(mem)
    unit = re.compile(r"[kmg]?b").search(mem)

    if value is None or unit is None:
        raise ValueError(f"Could not parse memory string: '{mem}'")

    conversion = dict(b = 1, kb = 1024, mb = 1024**2, gb = 1024**3)
    value = conversion[unit.group()] * int(value.group())

    return value


def walltime_to_secs(walltime: str) -> int:
    h, m, s = map(int, walltime.split(":"))
    seconds = h * 3600 + m * 60 + s

    return seconds


def secs_to_walltime(seconds: int) -> str:
    hours = seconds // 3600
    minutes = (seconds - hours * 3600) // 60
    seconds = (seconds - hours * 3600 - minutes * 60) // 1

    walltime = ":".join(
        [str(hours).zfill(2), str(minutes).zfill(2), str(seconds).zfill(2)]
    )

    return walltime

