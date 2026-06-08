
cleanup() {
    if [ -f "$WORKBENCH_FILE" ]; then
        rm "$WORKBENCH_FILE"
    fi
    exit 0  
}

trap cleanup SIGTERM

while true; do
    sleep 30  
done

exit 0
