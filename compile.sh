#PBS -N pbs-workbench-compile
#PBS -P lo70
#PBS -q normal
#PBS -l ncpus=4
#PBS -l mem=32GB
#PBS -l walltime=01:00:00
#PBS -l wd
#PBS -l jobfs=20GB
#PBS -l storage=gdata/lo70
#PBS -o logs/
#PBS -e logs/

set -eu
echo $(pwd)

module purge
echo Purged
module load patchelf
module load gcc/15.1.0
echo loaded patchelf and gcc

source .venv/bin/activate
echo loaded environment

#pip install -e .
echo installed pbs-workbench

python -m nuitka  \
 --onefile   \
 --include-package=job   \
 --include-data-files=src/job/data/idle.sh=job/data/idle.sh   \
 --include-package=urwid   \
 --output-filename=job   \
 --remove-output src/job/cli.py
