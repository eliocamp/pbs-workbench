#!/bin/bash

# this from the wd of the script. 
profile_folder=$HOME/pbs-workbench/profiles

echo "Creating new job profile..."
echo

read -p "Profile name [default: default]: " profile_name
profile_name=${profile_name:-default}


if [ -f "$profile_folder/${profile_name}.sh" ]; then
    read -p "A profile with that name already exists. Overwrite? [y/N]: " overwrite
    # Convert to lowercase and default to 'n'
    overwrite=$(echo "${overwrite:-n}" | tr '[:upper:]' '[:lower:]')
    if [ "$overwrite" != "y" ] && [ "$overwrite" != "yes" ]; then
        echo "Profile creation cancelled."
        exit 0
    fi
fi
# Project name
read -p "Project name [default: $PROJECT]: " project_name
project_name=${project_name:-$PROJECT}

# Walltime
read -p "Walltime [default: 8:00:00]: " walltime
walltime=${walltime:-8:00:00}

# CPUs
read -p "CPUs [default: 2]: " ncpus
ncpus=${ncpus:-2}

# Memory
read -p "Memory [default: 16GB]: " mem
mem=${mem:-16GB}

# Job filesystem
read -p "Job filesystem [default: 100GB]: " jobfs
jobfs=${jobfs:-100GB}

# Storage
read -p "Storage [default: gdata/$PROJECT]: " storage
storage=${storage:-gdata/$PROJECT}

mkdir -p $profile_folder

profile_file="$profile_folder/${profile_name}.sh"
# Generate the profile
cat > "$profile_file" << EOF
#!/bin/bash
#PBS -N ${profile_name}
#PBS -P ${project_name}
#PBS -l walltime=${walltime}
#PBS -l ncpus=${ncpus}
#PBS -l mem=${mem}
#PBS -l jobfs=${jobfs}
#PBS -l storage=${storage}
#PBS -l wd
#PBS -o $HOME/pbs-workbench/logs
#PBS -e $HOME/pbs-workbench/logs

bash idle.sh
EOF

echo "Profile created: $profile_file."