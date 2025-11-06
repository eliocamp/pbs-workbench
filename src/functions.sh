
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
   
    job_info=$(qstat -F json -f "$job_id")

    job_info=$(echo $job_info | jq '.Jobs[] | {
            walltime: .Resource_List.walltime, 
            mem: .Resource_List.mem,
            ncpus: .Resource_List.ncpus,
            queue: .queue
            }')

    walltime=$(get "$job_info" "walltime")
    walltime_seconds=$(walltime_to_seconds "$walltime")
    walltime_hours=$(bc -l <<< "$walltime_seconds / 3600")

    mem=$(get "$job_info" "mem")
    mem=${mem%"b"}
    GB=$((1024*1024*1024))
    mem=$(bc -l <<< "$mem / $GB / 4")

    ncpus=$(get "$job_info" "ncpus")

    resource=$(bc -l <<< "$mem < $ncpus")
    [[ $resource ]] && resource="$mem" || resource="$ncpus"

    queue=$(get "$job_info" "queue")
    queue=${queue%"-exec"}
    rate=${queues[${queue}]}

    su=$(bc -l <<< "$rate * $resource * $walltime_hours")
    echo $su
}