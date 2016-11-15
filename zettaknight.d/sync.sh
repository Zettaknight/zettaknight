#!/bin/bash
#
#    Copyright (c) 2015-2016 Matthew Carter, Ralph M Goodberlet.
#
#    This file is part of Zettaknight.
#
#    Zettaknight is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Zettaknight is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Zettaknight.  If not, see <http://www.gnu.org/licenses/>.
#
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
                nice -n $priority $ssh -q -i "$identity_file" "$remote_ssh" "$ssh_cmd"
            else
                echo "$identity_file is not accessible, cannot use"
                nice -n $priority $ssh -q $remote_ssh "$ssh_cmd"
            fi
        else
            nice -n $priority $ssh -q $remote_ssh "$ssh_cmd"
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
setopts var "-r|--remote_dataset" "remote_dataset" "remote_dataset name to be used"
setopts var "-s|--ssh" "remote_ssh" "Connection string for remote SSH connections, ie. root@somehost.somedomain.com"
setopts var "-i|--identity" "identity_file" "RSA identity file to use when initiating SSH connections.  Requires full path of identity file."
setopts var "-t|--timeout" "lock_file_exp" "if lock file still exists for -t hours, send an alert"
setopts var "-n|--priority" "priority" "nice level this script should run as"
setopts flag "-p|--pull" "pull_flag" "Replicates last snapshot from remote server to local server (pull replication instead of traditional push replication)."
setopts flag "-h|--help" "display_help_flag" "Shows this help dialogue."

#globals
date_time=$(date '+%Y%m%d_%H%M')
Local_output_dir="$running_dir"
remote_user=$(echo ${remote_ssh} | cut -d "@" -f1)
lock_file=$(echo "sync.${local_dataset}.lock" | tr -d "/")
lock_file_path=${Local_output_dir}/${lock_file}
remote_output_dir="/tmp"

if [ -z "$remote_dataset" ]; then
 
    remote_dataset="$local_dataset" #if no remote pool given, assume same as $local_dataset

fi

remote_host=$(echo ${remote_ssh} | cut -d "@" -f2)

if [ -z $lock_file_exp ]; then #if timeout not called set a default
    lock_file_exp=48 #hours until an alert will be sent about a existing lock file
fi
    
##################### check/create lockfile ######################
##################################################################
if [[ -f "$lock_file_path" ]]; then

    lock_file_mtime=$(stat -c %Y $lock_file_path)
    time_now=$(date +%s)
    lock_file_hours_old=$(( (time_now - lock_file_mtime) / 3600 ))
    
    if [ $lock_file_hours_old -gt $lock_file_exp ]; then
        echo "WARNING: lock file $lock_file_path for $local_dataset is older than $lock_file_exp hour(s), sync process cannot continue"
        exit 1
    else
        echo "ALERT: lock file $lock_file_path exists for $local_dataset, but is $lock_file_hours_old hour(s) old, which is within the limit set at $lock_file_exp"
        exit 0
    fi
else
    touch "$lock_file_path"
    check_previous "failed to create $lock_file_path"
fi

trap "{ rm -f $lock_file_path; exit; }" INT TERM EXIT
##################################################################
##################################################################

#determine call locations
find_call "zfs"
find_call "ssh"

if ! [[ $remote_user == "root" ]]; then #if remote user is not root, then assign a pseudo tty
    ssh="$ssh -t"
        zfs="sudo $zfs"
fi

if [[ -z "$local_dataset" ]] || [[ -z "$remote_ssh" ]]; then
    echo -e "\nrequired arguments missing\n"
    show_help
    exit 1
fi

################## check last snapshots ##########################
##################################################################
remote_snap=$(ssh_over $zfs list -r -o name -t snapshot -H "${remote_dataset}" | grep "${remote_dataset}@" | tail -n 1)
remote_last_snap=$(echo "$remote_snap" | tr -d '\r')
#num_remote_snaps=$(ssh_over $zfs list -o name -t snapshot -H | wc -l)
local_last_snap=$($zfs list -r -o name -t snapshot -H "${local_dataset}" | grep "${local_dataset}@" | tail -n 1)
#num_local_snaps=$($zfs list -o name -t snapshot -H | wc -l)
##################################################################
##################################################################

###################### non pull request ##########################
##################################################################
if [[ "$pull_flag" == 0 ]]; then

    if [ -z "$local_last_snap" ]; then
        echo "no snapshots exist, nothing to do"
        exit 0
    fi

    echo "syncing snapshots to $remote_host:"

    if ! ssh_over $zfs list -H "$remote_dataset" > /dev/null; then
        ssh_over $zfs create -p $remote_dataset
        check_previous ssh_over $zfs create -p $remote_dataset
        ssh_over logger -p info 'new zfs dataset created by remote process'
        echo "created $remote_dataset on $remote_host"
        sudo logger -p info "$0 created $remote_dataset on $remote_host"
        else
                echo "$remote_dataset exists, moving on"
    fi

    if [[ -z "$remote_last_snap" ]]; then #if no remote snapshot exists for dataset, then send them all
        $zfs send -R $local_last_snap | ssh_over "$zfs receive -F $remote_dataset"
        check_pipes "$zfs send -R $snap | ssh_over $remote_dataset"
        echo "Snapshot successfully shipped to $remote_host !"
    else
        
        if [[ "$local_dataset" == "$remote_dataset" ]]; then #if not equal translate is in play
        
            if [[ "$remote_last_snap" != "$local_last_snap" ]]; then
    
                $zfs send -R -I "$remote_last_snap" "$local_last_snap" | ssh_over "$zfs receive -F $remote_dataset"
                check_pipes "$zfs send -R -I $remote_last_snap $snap | ssh_over $zfs receive $remote_dataset"
                echo "snapshot successfully shipped to $remote_host!"
                
            else
            
                echo "$local_last_snap is the last snapshot on both systems"
                
            fi
            
        else
            
            local_last_snapshot="$(basename $local_last_snap)"
            local_last_snapshot_date="$(echo $local_last_snapshot | cut -d '@' -f 2)"
            local_last_snapshot_dir="$(echo $local_last_snapshot | cut -d '@' -f 1)"
            local_last_dir="$(dirname $local_last_snap)"
            remote_last_snapshot="$(basename $remote_last_snap)"
            remote_last_snapshot_date="$(echo $remote_last_snapshot | cut -d '@' -f 2)"
        
            if [[ "$local_last_snapshot_date" !=  "$remote_last_snapshot_date" ]]; then
                
                $zfs send -I "${local_last_dir}/${local_last_snapshot_dir}@${remote_last_snapshot_date}" "$local_last_snap" | ssh_over "$zfs receive -F $remote_dataset"
                check_pipes $zfs send -I "${local_last_dir}/${local_last_snapshot_dir}@${remote_last_snapshot_date}" "$local_last_snap" | ssh_over "$zfs receive -F $remote_dataset"
                echo "snapshot successfully translated from $local_last_snap to $remote_dataset on $remote_host!"
                
            else
            
                echo "$local_last_snap matches translated $remote_last_snap"
                
            fi
        fi
    fi
fi
##################################################################
##################################################################


###################### pull request ##############################
##################################################################
if [[ "$pull_flag" == 1 ]]; then 

    echo "pulling snapshots from: $remote_host:"

    if ! $zfs list -H "$local_dataset" > /dev/null; then
        $zfs create -p $remote_dataset
        check_previous $zfs create -p $remote_dataset
        logger -p info 'pull request from: ${remote_host} created $zfs dataset: $local_dataset'
        echo "pull request creates $zfs dataset: $local_dataset"
        sudo logger -p info "$0 created $local_dataset"
    fi


    if [[ -z $local_last_snap ]]; then #if local snapshot is empty
        ssh_over $zfs send -R "$remote_last_snap" | $zfs receive -F $local_dataset
        check_pipes "failed to pull initial snapshot"
        echo "Snapshot successfully retrieved from $remote_host !"
    else
        if ! [[ "$remote_last_snap" == "$local_last_snap" ]]; then
            ssh_over $zfs send -R -I "$local_last_snap" "$remote_last_snap" | $zfs receive -F $local_dataset
                        check_pipes "failed to pull incremental snapshot"
                        echo "Snapshot successfully retrieved from $remote_host !"    
        else
            echo "$local_last_snap is the last snapshot on both systems"
            #if ! [[ "$num_local_snaps" == "$num_remote_snaps" ]]; then
            #    echo "ERROR: $num_local_snaps snapshot(s) locally --- $num_remote_snaps snapshot(s) on ${remote_host}"
            #    exit 1
            #else
            #    echo "there are $num_local_snaps on both machines, filesystems are in sync" 
            #fi
        fi
    fi
fi

duration=$SECONDS

if [[ $duration -lt 3600 ]]; then
    if [[ $duration -gt 60 ]]; then
        duration=$(($duration / 60))
        echo "sync complete after $duration minute(s)"
    else
        echo "sync complete after $duration second(s)"
    fi
else
    duration=$(($duration / 3600))
    echo "sync complete after $duration hour(s)"
fi

##################################################################
##################################################################