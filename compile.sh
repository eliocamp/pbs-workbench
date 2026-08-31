
#PBS -P lo70
#PBS -q normal
#PBS -l ncpus=4
#PBS -l mem=32GB
#PBS -l walltime=01:00:00
#PBS -l wd
#PBS -l jobfs=20GB
#PBS -o logs/
#PBS -e logs/

module purge
module load patchelf
module load gcc/15.1.0
source .venv/bin/activate

pip install -e .

python -m nuitka  \
 --onefile   \
 --include-package=job   \
 --include-data-files=src/job/data/idle.sh=job/data/idle.sh   \
 --include-package=urwid   \
 --output-filename=job   \
 --remove-output src/job/cli.py