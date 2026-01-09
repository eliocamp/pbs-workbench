#!/bin/bash
set -eu
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source $SCRIPT_DIR/functions.sh

PROJECT_FILE="$HOME/pbs-workbench/project.job"

if [ -f "$PROJECT_FILE" ]; then
    job_id=$(get_job_id $PROJECT_FILE)
    exists=$(job_id_exists $job_id)
    if [ exists == 0 ]; then
        echo "Another job already running"
        echo "Monitor it with `job  monitor` or end it with `job end`."
        exit 1
    fi
fi

profile="${1:-"default"}"
profile_folder=$HOME/pbs-workbench/profiles
job_script="$profile_folder/${profile}.sh"

if [ ! -f $job_script ]; then
    echo "Job script $job_script not found"
    echo "Create a profile with job profile"
    exit 1
fi

echo Starting profile $job_script
JOB_ID=$(qsub "$job_script")

# Logs are saved here, make sure the folder exists
mkdir -p "$HOME/pbs-workbench/logs"

echo "${JOB_ID}" > "$PROJECT_FILE"
job monitor