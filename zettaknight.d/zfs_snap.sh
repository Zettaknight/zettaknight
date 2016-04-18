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

version="0.0.30"

#source helper functions
running_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
setopts="${running_dir}/setopts.sh"
source $setopts || { echo "failed to source $setopts"; exit 1; }

#authors
#Matthew Carter <mcarte4@clemson.edu>
#Ralph Goodberlet <rgoodbe@clemson.edu>

#current changes to write mail function and logfile information

#######################################
##### function declarations ###########
#######################################



function show_help () {
cat <<EOF

version $version

USAGE:
$0 [dsbmef]

DESCRIPTION:
        default protocol will use an /etc/xinetd.d/<file> daemon on remote server, you will need to use scp (-e) if this is not setup

OPTIONS:
        $setopts_help

EOF
}


function mail_out () {

    if [ $mail_flag == 1 ]; then
                local email_body="$@"

                if ! which mailx > /dev/null; then
                        echo "mailx does not exist in PATH, will not send email"
                        exit 1
                fi

                if [ -f "$email_body" ]; then
                        echo "message body cannot be a file, must be sent as an attachment using -a"
                        clean_up
                        show_help
                        exit 1
                fi

                echo "sending mail to $email_recipient"
                cat <<EOF | mailx -s "$email_subject" $email_recipient
                $email_body
EOF
                if [ $? -ne 0 ]; then
                        echo "failed to send mail to $email_recipient"
                fi

        fi
}

function clean_up () {
    if [ -f "$lock_file" ]; then
        rm -f "$lock_file"
        if [ $? -ne 0 ]; then
            echo "failed to delete $lock_file, clean up manually"
            exit 1
        fi
    fi
}

function check_previous () {
    local exit_status=$?
    local msg="$@"

    if ! [ $exit_status == 0 ]; then
        echo "${exit_status} : $@"
        mail_out $msg
        clean_up
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
                mail_out $msg
                clean_up
                exit 1
            else
                echo "$i : $failed"
                mail_out $msg
                clean_up
                exit 1
            fi
        fi
    n=$(( $n + 1 ))
    done
}

function find_call () {

    local call=$1
    local var_declare=$2 #what variable name you would like to set the call in $1 to be
    local need_sudo=$3 #if the user is not root, will it need sudo?

    local path=("/usr/local/sbin" "/usr/local/bin" "/sbin" "/bin" "/usr/sbin" "/usr/bin" "/root/bin")
    local found_flag=0


    for loc in ${path[@]}; do
        local full_path="${loc}/${call}"
        if [ $found_flag == 0 ]; then
            if [ -x $full_path ]; then
                #echo -e "${call}=${full_path}"
                found_flag=1

                if [ -z "$var_declare" ]; then
                    local final_call="$call"
                else
                    local final_call="$var_declare"
                fi

                if ! [ -z "$need_sudo" ]; then #if user is not root append sudo to each command
                    if [ $(id -u) != 0 ]; then
                        local full_path="sudo "${full_path}
                    fi
                fi

                eval $final_call"=\"\$full_path\""

            fi
        fi
    done


    if [ $found_flag == 0 ]; then
        echo -e "call $call not found, cannot continue"
        exit 1
    fi
}



function ssh_over () {
    ssh_cmd="$@"

    #if [ $(id -u) != 0 ]; then
    #    ssh="/bin/ssh -t"

    if [ -z "$identity_file" ]; then
        $ssh -q $remote_ssh "$ssh_cmd"
        #check_previous $ssh -q $remote_ssh "$ssh_cmd"
    else
        $ssh -q -i $identity_file $remote_ssh "$ssh_cmd"
        #check_previous $ssh -q -i $identity_file $remote_ssh "$ssh_cmd"
    fi

}

function xinetd_update () {
    local zfs_xinetd="/etc/xinetd.d/zfs"
    local userid=$(id -un)

        if [ -z $userid ]; then
                echo "no userid specified, must exit"
                exit 1
        fi

    ssh_arg="cat > $zfs_xinetd"
    if [ -z $identity_file ]; then
        ssh_cmd="ssh -q $remote_ssh $ssh_arg"
    else
        ssh_cmd="ssh -q -i $identity_file $remote_ssh $ssh_arg"
    fi

$ssh_cmd << EOF
# default: off
# listening on $nc_port to stream snapshot over netcat
service zfs
{
        disable = no
        type            = UNLISTED
        socket_type     = stream
        wait            = no
        user            = $userid
        server          = /opt/clemson/zfs_scripts/zfs_recv.sh
        server_args     = receive -F $local_dataset
        log_on_failure  += USERID
        port            = $nc_port
        instances       = 1
}
EOF

    $ssh_over $remote_service xinetd reload
    check_previous $ssh_over $remote_service xinetd reload
}

function failover_pre () {
    local verify_remote=$(ssh_over "uname") #verify remote is available
    if ! [ -z $verify_remote ]; then
        echo -e "\nFailover to $remote_host requested."
        $zfs set readonly=on ${local_dataset}
        check_previous "$zfs set readonly=on $local_dataset"
        echo "set dataset $local_dataset to read-only"

        if $local_service nfs status | grep nfsd | grep "is running" &> /dev/null; then
            $local_service nfs stop > /dev/null
            check_previous "$local_service nfs stop"
            echo "stopped nfs services"
        fi

        $zfs unmount $local_dataset
        check_previous "$zfs unmount $local_dataset"
        echo "unmounted dataset $local_dataset"
        $zfs mount $local_dataset
        check_previous "$zfs mount $local_dataset"re
        echo "mounted dataset $local_dataset"

        readonly_check=$($zfs get readonly | grep "$local_dataset " | awk '{print $3}')
        if ! [ $readonly_check == "on" ]; then
            echo "Failed to set dataset $local_dataset to readonly.  Pre-failover sync not attempted."
            clean_up
            exit 1
        fi
    fi
}

function failover () {
    ssh_over "$zfs set readonly=off ${remote_dataset}" > /dev/null
    check_previous "ssh_over $zfs set readonly=off ${remote_dataset}"
    echo "$remote_host: set dataset $remote_dataset to read-only"
        
    ssh_over "$zfs umount ${remote_dataset}" > /dev/null
    check_previous "ssh_over '$zfs umount ${remote_dataset}'"
    echo "$remote_host: umounted dataset $remote_dataset"
        
    ssh_over "$zfs mount ${remote_dataset}" > /dev/null
    check_previous "ssh_over '$zfs mount ${remote_dataset}'"
    echo "$remote_host: mounted dataset $remote_dataset"

    remote_readonly_check=$(ssh_over $zfs get readonly | grep "$local_dataset " | awk '{print $3}')
    echo "ssh_over $zfs get readonly | grep "$local_dataset " | awk '{print $3}'"
    if ! [ $remote_readonly_check == "off" ]; then
        echo "didn't remove dataset $remote_dataset readonly"
        clean_up
        exit 1
    fi
        
    #Comment out remote /etc/exports shares for local_dataset
    #ssh_over sed -i s@^/${local_dataset}@#/${local_dataset}@ /etc/exports > /dev/null
    #check_previous ssh_over "sed -i 's@^/${local_dataset}@#/${local_dataset}@' /etc/exports" > /dev/null
    #echo "$remote_host: commented out necessary shares in /etc/exports"
    tmp_file="/tmp/remote_exports.txt" #trash file to build /etc/exports without giving excessive permissions to non-root user
    remote_exports=$(ssh_over cat /etc/exports)
    echo $remote_exports > $tmp_file
    sed -i s@^/${local_dataset}@#/${local_dataset}@ $tmp_file
    check_previous sed -i s@^/${local_dataset}@#/${local_dataset}@ $tmp_file
    grep $local_dataset /etc/exports >> $tmp_file 
    check_previous grep $local_dataset /etc/exports >> $tmp_file
    
    cat $tmp_file | ssh_over 'cat > /etc/exports'
    check_previous "cat /tmp/remote_exports | ssh_over 'cat > /etc/exports'"

    #Append local /etc/exports shares to remote /etc/exports
    #grep "$local_dataset" /etc/exports | ssh_over "cat >> /etc/exports" > /dev/null
    #check_previous "grep "$local_dataset" /etc/exports | ssh_over "cat >> /etc/exports""
    #echo "$remote_host: appended local /ect/exports to $remote_host"
        

    #$ssh -q $remote_ssh "mv /etc/exports /etc/exports.pre_failover.${date_time}"
    #scp /etc/exports ${remote_ssh}:/etc/exports
    #check_previous "scp /etc/exports ${remote_ssh}:/etc/exports"
    ssh_over "$remote_service nfs restart"
    check_previous "ssh_over '$remote_service nfs restart'"
    echo "$remote_host: restarted NFS"
        
    echo -e "\nFailover to $remote_host completed :  <(o_0<) <(o_o)> (>0_o)> : This failover operation is dancing Kirby approved.\n"
}

function create_snap () {
    if $zfs list -o name -t snapshot -H | grep $snap; then
        echo "$snap already exists, moving on"
    else
        $zfs snapshot -r $snap
        check_previous "$zfs snapshot -r $snap"
        echo "created snapshot $snap"
    fi
}

function init_snap () {
    if [ $# == 1 ]; then
        local protocol=$1
    else
        echo "function init_snap : invalid arguments"
        exit 1
    fi

    if [ $protocol == "ssh" ]; then
                if [[ $pull_flag == 0 ]]; then
                $zfs send -R $snap | ssh_over "$zfs receive -F $remote_dataset"
                check_pipes "$zfs send -R $snap | ssh_over $remote_dataset"
                echo "Snapshot successfully shipped to $remote_host !"
                else
                        ssh_over "$zfs send -R $remote_last_snap" | $zfs receive -F $local_dataset
                        check_pipes "ssh_over $zfs send -R $remote_last_snap | $zfs receive -F $local_dataset"
                        echo "Snapshot successfully retrieved from $remote_host !"
                fi
    fi

    if [ $protocol == "nc" ]; then
        #ssh $remote_ssh "nc -l $nc_port | zfs receive -F $remote_dataset" &
        #check_pipes "ssh $remote_ssh nc -w 2 -l $nc_port | zfs receive -F $remote_dataset &"
        echo "starting backup... this may take some time..."
        echo "$zfs send -R $snap | nc $remote_host $nc_port"
        $zfs send -R $snap | nc $remote_host $nc_port
        check_pipes "$zfs send -R $remote_last_snap $snap | nc $remote_host $nc_port"
        echo "Snapshot successfully shipped to $remote_host !"
    fi
}

function inc_snap () {
    if [ $# == 1 ]; then
        local protocol=$1
    else
        echo "function inc_snap : arguments recieved ($#)"
        exit 1
    fi

    if [ $protocol == "nc" ]; then
        #ssh $remote_ssh "nc -w 10 -l $nc_port | $zfs receive -F $remote_dataset" &
        #check_pipes "ssh $remote_ssh nc -w 10 -l $nc_port | $zfs receive -F $remote_dataset &"
        $zfs send -R -I $remote_last_snap $snap | nc $remote_host $nc_port
        check_pipes "$zfs send -R -I $remote_last_snap $snap | nc $remote_host $nc_port"
        echo "Snapshot successfully shipped to $remote_host !"
    fi

    if [ $protocol == "ssh" ]; then
                if [[ $pull_flag == 0 ]]; then
                $zfs send -R -I $remote_last_snap $snap | ssh_over "$zfs receive -F $remote_dataset"
                check_pipes "$zfs send -R -I $remote_last_snap $snap | ssh_over $zfs receive $remote_dataset"
                echo "snapshot successfully shipped to $remote_host!"
                else
                        ssh_over "$zfs send -R -I $last_snap_local $remote_last_snap" | $zfs receive -F $local_dataset
                        check_pipes "ssh_over $zfs send -R -I $last_snap_local $remote_last_snap | $zfs receive -F $local_dataset"
                        echo "Snapshot successfully retrieved from $remote_host !"
                fi
    fi
}

function local_snap () {
    $zfs send -R $snap > ${Local_output_dir}/${snap_file}
    check_previous "$zfs send -R $snap > ${Local_output_dir}/${snap_file}"
    echo "$snap_file successfully saved to ${Local_output_dir}/${snap_file}"
}

#######################################
################# flags ###############
#######################################
backup_only=0
encrypt_flag=0
failover_flag=0
mail_flag=0 #0 no mail, 1 mail out
display_help_flag=0
send_flag=0

#######################################
########### script start ##############
#######################################


#setopts vars
setopts var "-d|--dataset" "local_dataset" "local_dataset to be replicated"
setopts var "-b|--backup_dir" "backup_dir" "set a backup location if replication is to occur locally, this can be used in conjunction with the other options"
setopts var "-s|--ssh" "remote_ssh" "Connection string for remote SSH connections, ie. root@somehost.somedomain.com"
setopts var "-i|--id_file" "identity_file" "RSA identity file to use when initiating SSH connections.  Requires full path of identity file."
setopts flag "-e|--encrypt" "encrypt_flag" "this option will flag zettaknight to use the ssh protocol for replication"
setopts flag "-f|--failover" "failover_flag" "Initiates a controlled failover to remote target, in addition to taking and replicating a new snapshot"
setopts flag "-r|--replicate_only" "replicate_only_flag" "Replicates current snaps to remote ssh target without first taking a new snap."
setopts flag "-p|--pull" "pull_flag" "Replicates last snapshot from remote server to local server (pull replication instead of traditional push replication).  -r must also be specified."
setopts flag "-h|--help" "display_help_flag" "Shows this help dialogue."

if [ $display_help_flag == 1 ]; then
    show_help
    clean_up
    exit 1
fi

#######################################
############ global var ###############
#######################################
date_time=$(date '+%Y%m%d_%H%M')
Local_output_dir="$running_dir"
remote_user=$(echo ${remote_ssh} | cut -d "@" -f1)

#determine call locations
find_call "service" "local_service" #find the full path of service and set it equal to the variable local_service
find_call "zfs"
find_call "ssh"

if ! [ -z "$remote_ssh" ]; then #if not a local backup define remote variables
    remote_service=$(declare -f | ssh -i $identity_file $remote_ssh "$(cat);find_call service" | cut -d "=" -f 2)
    if [ -z "$remote_service" ]; then
        echo "variable remote_service could not be determined, trying $local_service"
        remote_service="$local_service"
    fi
fi
#######################################

if ! [[ $remote_user == "root" ]]; then #if remote user is not root, then assign a pseudo tty
    ssh="$ssh -t"
        zfs="sudo $zfs"
fi

remote_host=$(echo ${remote_ssh} | cut -d "@" -f2)
if [ -z "$remote_host" ]; then
    echo "remote host is empty, -s should be in the format of <user>@<hostname>, recieved: $remote_ssh"
        show_help
        clean_up
    exit 1
fi

lock_file="${Local_output_dir}/zfs_snap.lock"
nc_port=8023
remote_output_dir="/tmp"
remote_dataset=${local_dataset} #if no remote pool given, assume same as $local_dataset
snap="${local_dataset}@${date_time}"
snap_file="${date_time}_localsnapfile.img"
remote_snap=$(ssh_over "$zfs list -o name -t snapshot -H | grep ${remote_dataset}@ | tail -1")
remote_last_snap=$(echo "$remote_snap" | tr -d '\r')
last_snap_local=$($zfs list -o name -t snapshot -H | grep ${remote_dataset}@ | tail -1)




############## mail information ##############
##############################################
email_subject="$(hostname)_cmd_failed"
email_recipient="mcarte4@clemson.edu rgoodbe@clemson.edu"

#trap ctrl+c so clean_up function is run on ctrl+c
trap "{ clean_up; exit }" INT TERM

############################################
### check required arguments ###############
############################################

if [ $(id -u) != 0 ]; then
    echo "$0 need to be ran with the root user"
    exit 1
fi


if [ -z $local_dataset ]; then
        show_help
        clean_up
        exit 1
fi

if ! [ -z "$backup_dir" ]; then #if backup_dir is specified
    #if no remote ssh option given, the local backup only will be performed
    if [ -z "$remote_ssh" ]; then
        backup_only=1
        echo "No remote host was specified.  Performing local backup only."
    fi
else
    #if remote ssh not given and backup_dir not specified, nothing to do, show help, clean and exit
    if [[ -z $remote_ssh ]]; then
        echo "-b and/or -s must be used, exiting"
        show_help
        clean_up
        exit 1
    fi
fi

#failover is not possible without remote ssh, nothing to do, show help, clean and exit
if [[ -z "$remote_ssh" ]] && [[ $failover_flag == 1 ]]; then
    echo -e "Remote server must be specified when requesting a failover."
    show_help
    clean_up
    exit 1
fi

if [[ $replicate_only_flag == 0 ]] && [[ $pull_flag == 1 ]]; then
        echo -e "Replicate only (-r) must be specified when requesting snapshot retrieval (pull, -p)."
        show_help
        clean_up
        exit 1
fi

#if the lock file exists, then another instance is already running, exit.  Else create
#the lock file and continue
if [ -f "$lock_file" ]; then
        echo "$lock_file exists, cannot start backup for $local_dataset"
        mail_out "$lock_file exists, cannot start backup for $local_dataset"
        exit 1
else
        touch $lock_file
        check_previous "touch $lock_file"
fi

############################################
### end check required arguments ###########
############################################

#If failover specified, set local dataset readonly and stop NFS services
#local pool must be set to read-only before taking a snapshot
if [ $failover_flag == 1 ]; then
    failover_pre
fi

#If all checks have passed, create a snap
if [ $replicate_only_flag == 0 ]; then
    create_snap
else
    if [[ $pull_flag == 0 ]]; then
                echo "$(hostname) is not the primary, syncing snapshots to $remote_host"
        else
                echo "$(hostname) is not the primary, retrieving snapshots from $remote_host"
        fi
        snap="$last_snap_local"
    if [[ "$snap" == "$remote_last_snap" ]]; then
        send_flag=1
                if [[ $pull_flag == 0 ]]; then
                echo "Remote server is already up to date!  No snaps to send."
                else
                        echo "Local server is already up to date!  No snaps to retrieve."
                fi
    fi
fi


#If backup location was specified, send snap to backup location
if ! [ -z "$backup_dir" ]; then #if backup_dir was specified
    local_snap
    if [ -e "$backup_dir" ]; then
        Local_output_dir="$backup_dir"
        if [ ! -d "$Local_output_dir" ]; then
            echo -e "Specified backup directory does not exist!"
            show_help
            clean_up
            exit 1
        fi
    fi
fi

#Verify dataset structure exists on remote host
#check remote dataset, if remote dataset does not exist, create it
echo "checking to see if $remote_dataset exists on $remote_host"
if ! ssh_over $zfs list $remote_dataset > /dev/null; then
        if [[ $pull_flag == 0 ]]; then
            echo "creating remote dataset $remote_dataset on $remote_host"
            ssh_over $zfs create -p $remote_dataset
            check_previous ssh_over $zfs create -p $remote_dataset
            ssh_over logger -p info 'new zfs dataset created by remote process'
            echo "created $remote_dataset on $remote_host"
            sudo logger -p info "$0 created $remote_dataset on $remote_host"
        else
                echo "$remote_dataset does not exist on ${remote_host}.  Cannot retrieve last snapshot."
                clean_up
                exit 1
        fi
else
    echo "$remote_dataset exists on $remote_host"
fi


if [ $encrypt_flag == 0 ]; then #Set transfer protocol based on encryption setting
    xinetd_update
    xfer="nc"
else
    xfer="ssh"
fi

#If remote server has previous snaps, send an incremental, otherwise send a full

if [[ $pull_flag == 0 ]] && [ -z $remote_last_snap ]; then
           init_snap $xfer
elif [[ $pull_flag == 1 ]] && [ -z $last_snap_local ]; then
        init_snap $xfer
else
           if [[ $send_flag == 0 ]]; then
               inc_snap $xfer
           fi
fi

if [ $failover_flag == 1 ]; then
    failover
fi

clean_up
