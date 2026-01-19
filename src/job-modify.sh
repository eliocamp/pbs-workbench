#!/bin/bash
set -eu


profile_folder=$HOME/pbs-workbench/profiles

profile="${1:-"default"}"

job_script="$profile_folder/${profile}.sh"

if [ ! -f $job_script ]; then
    echo "Job script $job_script not found"
    echo "Create a profile with job profile"
    exit 1
fi

${EDITOR:-vim} "$job_script"