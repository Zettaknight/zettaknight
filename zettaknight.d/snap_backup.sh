#!/bin/bash
#set -x

SECONDS=0 #bash built in

echo "sync process started: $(date)"

#source helper functions
running_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
setopts="${running_dir}/setopts.sh"
find_call="${running_dir}/find_call.sh"
source $setopts || { echo "failed to source $setopts"; exit 1; }
source $find_call || { echo "failed to source $find_call"; exit 1; }

function check_previous () {
    local exit_status=$?
    local msg="$@"

    if ! [ $exit_status == 0 ]; then
        echo "${exit_status} : $@"
        exit 1
    fi
}

function check_pipes () {
    local pipe_exit_status=$(echo ${PIPESTATUS[*]})
    local msg="$@"
    n=1
    for i in $pipe_exit_status; do
        if ! [ $i == 0 ]; then
            failed=$(echo "$msg" | cut -d "|" -f${n})
            echo "$@"
            if [ $i == 141 ]; then
                echo "Failed to pipe output of command: $failed"
                exit 1
            else
                echo "$i : $failed"
                exit 1
            fi
        fi
    n=$(( $n + 1 ))
    done
}

function ssh_over () {
    ssh_cmd="$@"

    if ! [ -z "$priority" ]; then

        if ! [[ -z "$identity_file" ]]; then
            if [[ -f "$identity_file" ]]; then
                $ssh -q -i "$identity_file" "$remote_ssh" "$ssh_cmd"
            else
                echo "$identity_file is not accessible, cannot use"
                $ssh -q $remote_ssh "$ssh_cmd"
            fi
        else
            $ssh -q $remote_ssh "$ssh_cmd"
        fi

    else

        if ! [[ -z "$identity_file" ]]; then
            if [[ -f "$identity_file" ]]; then
                $ssh -q -i "$identity_file" "$remote_ssh" "$ssh_cmd"
            else
                echo "$identity_file is not accessible, cannot use"
                $ssh -q $remote_ssh "$ssh_cmd"
            fi
        else
            $ssh -q $remote_ssh "$ssh_cmd"
        fi

    fi


}

#setopts vars
setopts var "-d|--dataset" "local_dataset" "local_dataset to be replicated"
setopts var "-r|--remote_dump" "remote_dump" "directory where we're going to put the dump we've taken"
setopts var "-s|--ssh" "remote_ssh" "Connection string for remote SSH connections, ie. root@somehost.somedomain.com"
setopts var "-i|--identity" "identity_file" "RSA identity file to use when initiating SSH connections.  Requires full path of identity file."
setopts var "-t|--timeout" "lock_file_exp" "if lock file still exists for -t hours, send an alert"
setopts flag "-h|--help" "display_help_flag" "Shows this help dialogue."

#globals
date_time=$(date '+%Y%m%d_%H%M')
Local_output_dir="$running_dir"
remote_user=$(echo ${remote_ssh} | cut -d "@" -f1)
lock_file=$(echo "sync.${local_dataset}.lock" | tr -d "/")
lock_file_path=${Local_output_dir}/${lock_file}
remote_output_dir="/tmp"
remote_host=$(echo ${remote_ssh} | cut -d "@" -f2)

#determine call locations
find_call "zfs"
find_call "ssh"

unset local_snap_array
for snap in $($zfs list -r -o name -t snapshot -H "${local_dataset}"); do

    local_snap_array+=("$snap")

done

unset remote_dump_array
for snap in $(ssh_over ls $remote_dump | grep ${local_dataset}@); do

    remote_dump_array+=("$snap")

done

#Have we dumped here before?
local_last_snapshot=${local_snap_array[${#local_snap_array[@]}-1]}
local_last_snap=$(echo $local_last_snapshot | awk -F '/' '{print $NF}') #get just the snapshot, not the full path

if ! [ -z "$local_last_snapshot" ]; then #if a local snapshot exists

    if [ "${#remote_dump_array[@]}" -ge 1 ]; then #if a remote snapshot exists
    
        remote_last_dump=${remote_dump_array[${#remote_dump_array[@]}-1]}
    
        if [ "$local_last_snapshot" != "$remote_last_dump" ]; then #if the local last snap is not the same as the last remote
            
            for dump in ${remote_dump_array[@]}; do
            
                if [" ${local_dump_array[@]} " =~ ${dump} ]; then
            
                    last_match="$snap"
                    
                fi
                
            done

        fi

    fi

    if [ -z "$last_match" ]; then
    
        echo "sending $local_last_snapshot to ${remote_host}:${remote_dump}/${local_last_snap}"
        $zfs send $local_last_snapshot | ssh_over "cat > ${remote_dump}/${local_last_snap}"
        check_previous $zfs send $local_last_snapshot | ssh_over "cat > ${remote_dump}/${local_last_snap}"
        
    else
    
        echo "sending $last_match --> $local_last_snapshot to ${remote_host}:${remote_dump}/${local_last_snap}"
        $zfs send -I "$last_match" "$local_last_snapshot" | ssh_over "cat > ${remote_dump}/${local_last_snap}"
        check_previous $zfs send -I "$last_match" "$local_last_snapshot" | ssh_over "cat > ${remote_dump}/${local_last_snap}"

    fi

else

    echo "no snapshots for $local_dataset, dump is not necessary"
    exit 0

fi
