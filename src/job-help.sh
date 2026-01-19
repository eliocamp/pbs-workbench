#!/bin/bash

cat << 'EOF'
PBS Workbench - Interactive PBS Job Management

USAGE:
    job <command> [options]
    job --help|-h

COMMANDS:
    start [profile]     Start a new PBS job with optional profile (default: "default")
    monitor             Monitor the current running job with real-time updates
    end                 Stop the current running job and clean up
    profile [name]      Create or modify a job profile interactively
    su [profile|file]   Calculate PBS service units for cost estimation
    modify [profile|file] Edits the profile in the default editor (set with $EDITOR) or vim

OPTIONS:
    --help, -h          Show this help message

EXAMPLES:
    job profile                    # Create a new profile interactively
    job start                      # Start a job with default profile
    job start myprofile            # Start a job with specific profile
    job monitor                    # Monitor current job status
    job end                        # Stop current job
    job su                         # Calculate service units for default profile
    job su job.sh                  # Calculate service units for a custom job.sh file
    job modify                       # Edit the default profile
    
EOF