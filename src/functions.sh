
get_job_id() {
    PROJECT_FILE=$1
    if [ ! -f "$PROJECT_FILE" ]; then
        return 1
    fi
    read id < $PROJECT_FILE
    echo "$id"
}


job_id_exists() {
    code=$(qstat -f $1)    
    if [ $? == 0 ]; then   
        echo  0
        return 0
    fi
    echo 1
}


walltime_to_seconds() {
    local walltime=$1
    IFS=':' read -r hours minutes seconds <<< "$walltime"
    total_seconds=$((10#$hours * 3600 + 10#$minutes * 60 + 10#$seconds))
    echo $total_seconds
}

get() {
    local json="$1"
    local variable="$2"
    echo "$json" | jq -r ".$variable // empty"
}

su_from_id() {
    local job_id=$1
    declare -A queues

    queues["normal"]=2
    queues["express"]=6
    queues["hugemem"]=3
    queues["megamem"]=5
    queues["gpuvolta"]=3
    queues["normalbw"]=1.25
    queues["expressbw"]=3.75
    queues["normalsl"]=1.5
    queues["hugemembw"]=1.25
    queues["megamembw"]=1.25
    queues["copyq"]=2
    queues["dgxa100"]=4.5
    queues["normalsr"]=2
    queues["expresssr"]=6
   
    local job_info=$(qstat -F json -f "$job_id")

    job_info=$(echo $job_info | jq '.Jobs[] | {
            walltime: .Resource_List.walltime, 
            mem: .Resource_List.mem,
            ncpus: .Resource_List.ncpus,
            queue: .queue
            }')

    local walltime=$(get "$job_info" "walltime")
    local walltime_seconds=$(walltime_to_seconds "$walltime")
    local walltime_hours=$(bc -l <<< "$walltime_seconds / 3600")

    local mem=$(get "$job_info" "mem")
    mem=${mem%"b"}
    local GB=$((1024*1024*1024))
    mem=$(bc -l <<< "$mem / $GB / 4")

    local ncpus=$(get "$job_info" "ncpus")

    local resource=$(bc -l <<< "$mem < $ncpus")

    if [[ $resource -eq 1 ]]; then 
        # Asking for more CPUs than mem
        resource=$ncpus
        # Can ask for more memory        
        local ceiling=$(bc -l <<< "$ncpus * 4")
        local unit_ceiling="GB RAM"

        # Or fewer CPUs
        local floor=$(bc -l <<< "$mem * 4")
        local unit_floor="CPUs"

    else
        # Asking for more mem than CPUs
        resource=$mem
        # Can ask for more CPUs
        local ceiling=$mem
        local unit_ceiling="CPUs"

        # Or less RAM
        local floor=$(bc -l <<< "$ncpus * 4")
        local unit_floor="GB RAM"
    fi

    local full_use=$(bc -l <<< "$mem == $ncpus")

    if [[ $full_use -eq 1 ]]; then
        local advice="Optimal memory and CPU request."
    else 
        ceiling=$(printf "%.0f" "$ceiling")
        floor=$(printf "%.0f" "$floor")
        
        local advice="Can increase $unit_ceiling to $ceiling or reduce $unit_floor to $floor."
    fi
    
    local queue=$(get "$job_info" "queue")
    queue=${queue%"-exec"}
    local rate=${queues[${queue}]}

    local su=$(bc -l <<< "$rate * $resource * $walltime_hours")
    printf '%s\n' "$su" "$advice"
}