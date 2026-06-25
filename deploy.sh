# This needs to be run on a compute node
python -m nuitka  \
 --onefile   \
 --include-package=job   \
 --include-data-files=src/job/data/idle.sh=job/data/idle.sh   \
 --include-package=urwid   \
 --output-filename=job   \
 --remove-output \ 
 src/job/cli.py
