PROJECT_FILE="$HOME/pbs-workbench/project.job"

cleanup() {
    if [ -f "$PROJECT_FILE" ]; then
        rm "$PROJECT_FILE"
    fi
    exit 0  
}

trap cleanup SIGTERM

while true; do
    sleep 30  
done

exit 0
