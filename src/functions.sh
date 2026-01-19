
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
    declare -A queue_rates

    queue_rates["normal"]=2
    queue_rates["express"]=6
    queue_rates["hugemem"]=3
    queue_rates["megamem"]=5
    queue_rates["gpuvolta"]=3
    queue_rates["normalbw"]=1.25
    queue_rates["expressbw"]=3.75
    # queue_rates["normalsl"]=1.5
    queue_rates["hugemembw"]=1.25
    queue_rates["megamembw"]=1.25
    queue_rates["copyq"]=2
    # queue_rates["dgxa100"]=4.5
    # queue_rates["normalsr"]=2
    # queue_rates["expresssr"]=6
    
    declare -A queue_ram_per_cpu

    queue_ram_per_cpu["normal"]=4
    queue_ram_per_cpu["express"]=4
    queue_ram_per_cpu["hugemem"]=31
    queue_ram_per_cpu["megamem"]=62
    queue_ram_per_cpu["gpuvolta"]=8
    queue_ram_per_cpu["normalbw"]=9
    queue_ram_per_cpu["expressbw"]=9
    # queue_ram_per_cpu["normalsl"]=1.5
    queue_ram_per_cpu["hugemembw"]=37
    queue_ram_per_cpu["megamembw"]=47
    queue_ram_per_cpu["copyq"]=2
    # queue_ram_per_cpu["dgxa100"]=4.5
    # queue_ram_per_cpu["normalsr"]=2
    # queue_ram_per_cpu["expresssr"]=6

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
    local queue=$(get "$job_info" "queue")
    queue=${queue%"-exec"}

    local mem=$(get "$job_info" "mem")
    mem=${mem%"b"}
    local GB=$((1024*1024*1024))
    local ram_per_cpu=${queue_ram_per_cpu[${queue}]}
    mem=$(bc -l <<< "$mem / $GB / $ram_per_cpu")

    local ncpus=$(get "$job_info" "ncpus")

    local resource=$(bc -l <<< "$mem < $ncpus")

    if [[ $resource -eq 1 ]]; then 
        # Asking for more CPUs than mem
        resource=$ncpus
        # Can ask for more memory        
        local ceiling=$(bc -l <<< "$ncpus * $ram_per_cpu")
        local unit_ceiling="GB RAM"

        # Or fewer CPUs
        local floor=$(bc -l <<< "$mem * $ram_per_cpu")
        local unit_floor="CPUs"

    else
        # Asking for more mem than CPUs
        resource=$mem
        # Can ask for more CPUs
        local ceiling=$mem
        local unit_ceiling="CPUs"

        # Or less RAM
        local floor=$(bc -l <<< "$ncpus * $ram_per_cpu")
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
    
    local rate=${queue_rates[${queue}]}

    local su=$(bc -l <<< "$rate * $resource * $walltime_hours")
    printf '%s\n' "$su" "$advice"
}