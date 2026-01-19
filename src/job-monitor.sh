#!/bin/bash

update_seconds=10
if [ -z "$WATCH_RUNNING" ]; then
    export WATCH_RUNNING=1
    exec watch -c -t -n $update_seconds bash "$0"
fi

# PBS Job Monitor CLI
# Usage: ./monitor_job.sh
# Reads job info from project.job file
SCRIPT_NAME=$(basename "$0")
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_FILE="$HOME/pbs-workbench/project.job"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to build colored output (returns string instead of printing)
build_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to convert seconds to human readable time
seconds_to_time() {
    local seconds=$1
    local hours=$((seconds / 3600))
    local minutes=$(((seconds % 3600) / 60))
    local secs=$((seconds % 60))
    printf "%02d:%02d:%02d" $hours $minutes $secs
}

source $SCRIPT_DIR/functions.sh

# Function to get job info from qstat
get_job_info() {
    local job_id=$1    
    local job_info=$(qstat -F json -f "$job_id")

    if [ $? -ne 0 ]; then
        return 1
    fi

    # Extract only the info we need
    echo $job_info | jq '.Jobs[] | {
        job_state, 
        walltime: .Resource_List.walltime, 
        used_walltime: .resources_used.walltime, 
        queue, 
        hostname: ((.exec_host // "/") | split("/")[0]),
        comment
        }'
}

monitor_header() {
    local header=""
    header+=$hline
    header+="\n"
    header+=$(build_status "$BLUE" "           PBS Workbench Monitor")
    header+="\n"
    header+=$hline
    header+="\n\n"
    echo $header
}

# Main monitoring function
monitor_job() {
    local output=""
    local term_width=$(tput cols)
    hline=$(build_status "$BLUE" "$(printf '=%.0s' $(seq 1 $term_width))")

    # Build header
    output+=$(monitor_header)
    
    # Check for project.job file
    if [ ! -f "$PROJECT_FILE" ]; then
        output+=$(build_status "$RED" "❌ No project.job file found")
        output+="\n\n"
        output+=$(build_status "$YELLOW" "Make sure you're in the directory where you submitted the job")
        output+="\n"
        output+=$(build_status "$YELLOW" "and that the job has started running.")
        
        # Clear screen and print all at once
        clear
        echo -e "$output"
        return 1
    fi
    
    # Read project file
    local job_id=$(get_job_id $PROJECT_FILE)
    if [ $? -ne 0 ]; then
        output+=$(build_status "$RED" "❌ Failed to read project.job file")
        
        # Clear screen and print all at once
        clear
        echo -e "$output"
        return 1
    fi

    mapfile -t out < <(su_from_id "$jobid")
    local su="${out[0]}"
    local su=$(printf "%0.0f\n" $su)

    output+=$(build_status "$CYAN" "📍 Job ID: $job_id")
    output+="\n"
    output+=$(build_status "$CYAN" "💸 Usage: ${su}SU")
    output+="\n"

    # Get job status from qstat
    local job_status_data=$(get_job_info "$job_id")
    if [ $? -ne 0 ]; then
        # Job not found in qstat - probably completed or killed
        output+="\n"
        output+=$(build_status "$YELLOW" "⚠️  Job not found in queue (completed or terminated)")
        output+="\n"
        # Clear screen and print all at once
        clear
        echo -e "$output"
        return 0
    fi
    
    local job_state=$(get "$job_status_data" "job_state")
    
    output+="\n"
    
    # Show status based on job state
    case "$job_state" in
        "Q")
            output+=$(build_status "$YELLOW" "⏳ Status: QUEUED - Waiting for job to run")
            output+="\n"
            local comment=$(get "$job_status_data" "comment")        
            output+=$(build_status "$YELLOW" "   Reason: $comment")
            ;;
        "R")
            local hostname=$(get "$job_status_data" "hostname")
            wd=$(pwd)
            output+=$(build_status "$GREEN" "🚀 Status: RUNNING on node $hostname")
            output+="\n\n"
            output+=$(build_status "$GREEN" "   SSH command: \n     ssh -X $hostname")
            output+="\n"
            output+=$(build_status "$GREEN" "   SSH tunnel: \n     ssh -L 8080:127.0.0.1:8080 $USER@$hostname")
            output+="\n"
            output+=$(build_status "$GREEN" "   Remote-ssh: \n     --remote ssh-remote+$hostname $wd")
            output+="\n"

    
            # Calculate runtime based on project.job start time
            local walltime=$(get "$job_status_data" "walltime")
            local used_walltime=$(get "$job_status_data" "used_walltime")
            local queue=$(get "$job_status_data" "queue")
            # Show time information
            if [ -n "$walltime" ]; then
                walltime_seconds=$(walltime_to_seconds "$walltime")

                if [ -n "$used_walltime" ] && [ "$job_state" = "R" ]; then
                    used_seconds=$(walltime_to_seconds "$used_walltime")
                    remaining_seconds=$((walltime_seconds - used_seconds))
        
                    if [ $remaining_seconds -gt 0 ]; then
                        local remaining=$(seconds_to_time $remaining_seconds)
                        # Show progress bar
                        local progress=$((used_seconds * 20 / walltime_seconds))
                        local bar=$(printf "%*s" $progress | tr ' ' '#')
                        local empty=$(printf "%*s" $((20 - progress)) | tr ' ' '-')
                        output+="\n"
                        output+=$(build_status "$BLUE" "   Progress: $used_walltime [$bar$empty] $remaining $((used_seconds * 100 / walltime_seconds))%")                       
                    else
                        output+="\n"
                        output+=$(build_status "$RED" "⚠️  Time exceeded!")
                    fi
                fi
            fi
            ;;
        "H")
            output+=$(build_status "$YELLOW" "⏸️  Status: HELD - Job is on hold")
            ;;
        *)
            output+=$(build_status "$YELLOW" "❓ Status: $job_state")
            ;;
    esac
    
    output+="\n\n"
    output+=$hline
    output+="\n"
    output+=$(build_status "$YELLOW" "Updates every $update_seconds seconds")
    
    # Clear screen and print everything at once
    echo -e "$output"
}

# Main script
main() {
    if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
        echo "PBS Job Monitor"
        echo "Usage: $SCRIPT_NAME"
        echo
        echo "Monitors the job defined in project.job file"
        echo "Run this in the same directory where you submitted your PBS job"
        echo "Press Ctrl+C to exit the monitor"
        exit 0
    fi
    
    # Check if qstat is available
    if ! command -v qstat &> /dev/null; then
        build_status "$RED" "❌ Error: qstat command not found"
        build_status "$YELLOW" "This script requires PBS/Torque to be installed"
        exit 1
    fi
    
    # Show initial content immediately
    monitor_job
    
}

# Run main function with cleanup on exit
main "$@"
