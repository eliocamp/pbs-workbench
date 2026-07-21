# This needs to be run on a compute node
module purge
module load patchelf
module load gcc/15.1.0

python -m nuitka  \
 --onefile   \
 --include-package=job   \
 --include-data-files=src/job/data/idle.sh=job/data/idle.sh   \
 --include-package=urwid   \
 --output-filename=job   \
 --remove-output src/job/cli.py