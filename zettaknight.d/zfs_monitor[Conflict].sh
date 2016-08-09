#!/bin/bash
#set -x 
version="0.0.18"


#authors
#Matthew Carter <mcarte4@clemson.edu>
#Ralph Goodberlet <rgoobe@clemson.edu>

###############################################################################
###############################################################################
#####################  Function Declarations  #################################
###############################################################################
###############################################################################


#source helper functions
running_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
setopts="${running_dir}/setopts.sh"
replace_disks="${running_dir}/replace_disk.sh"
mail_out="${running_dir}/mail_out.sh"

source $setopts || { echo "failed to source $setopts"; exit 1; }

if ! [ -x "$replace_disks" ] || ! [ -x "$mail_out" ]; then
        echo "failed to source $replace_disks or $mail_out, check paths"
        exit 1
fi



function show_help () {
cat << EOF
version $version

    DESCRIPTION:
                $(basename $0) used to monitor zfs systems, checks multipath, xinted, and
                zpool health check.

                This utility is intended to be run as a regularly scheduled cron job and
                must be run as root.

    $setopts_help
EOF
}

function check_previous () {
        if [ $? -ne 0 ]; then
                echo -e "\n$?: $@\n" | tee -a "$logfile"
                $mail_out "$(hostname) is degraded --- error : $0"
                if [ -e "$logfile" ]; then
                        rm -f "$logfile"
                fi
                exit 1
        fi
}

###############################################################################
###############################################################################
#####################  Global Variables  ######################################
###############################################################################
###############################################################################
date_time=$(date +'%Y%m%d')
logfile="$0.log_${date_time}"
email_subject="$(hostname)" #variable is appended to throughout the script


### flags ####
error_flag=0
mpath_error_flag=0
disk_error_flag=0
percent_use_flag=0


#mail_flag=1
exe_user=$(cat /etc/passwd | grep $(id -u) | cut -d ":" -f1)
zpool="/sbin/zpool"
multipath="/sbin/multipath"
service="/sbin/service"
zpool_capacity_limit=80 #alert value when zpool used capacity is above this limit
scrub_days_old=8
scrubExpire=$(( $scrub_days_old * 86400 ))

###############################################################################
###############################################################################
#####################  Script Start  ##########################################
###############################################################################
###############################################################################

#setopts flag "-q|--quiet" "mail_flag" "this option suppresses the mail output of the script"
setopts var "-p|--protocol" "protocol" "snapshot sending protocol for $(basename $0) to check against, currently supports xinetd and ssh"
setopts var "-r|--recipient" "message_recipient" "who to send email to in the event of an error"

if [ $(id -u) != 0 ]; then #check if ran as root user
                echo "$0 needs to be ran as root" | tee -a "$logfile"
                error_flag=1
                $mail_out "$(hostname) : $exe_user attempted to run $0"
                exit 1
fi

echo -e "\ntesting health of the zpool"
if $zpool status -x | grep -v "all pools are healthy" &> /dev/null; then
        error_flag=1
    email_subject="$email_subject: zpool is not healthy"
        $zpool status -x | tee -a "$logfile"
        check_previous "$zpool status -x | tee -a $logfile"
    echo -e "\nchecking to see if any disks are in a failed status, if spares are defined a resilver will be started"
    $replace_disks | tee -a "$logfile"
    check_previous "failed to issue replacement of failed disk, via $replace_disks"
else
    echo "all pool(s) healthy"
fi

#check for disk errors
echo -e "\nchecking for errors on disks currently ONLINE for zpool"
disk_err_array=()
while read line; do
        disk=$(echo $line | awk '{print $1}')
        read_err=$(echo $line | awk '{print $3}')
        write_err=$(echo $line | awk '{print $4}')
        chk_sum_err=$(echo $line | awk '{print $5}')
        
        out_string="$disk"
        if [[ $read_err != 0 ]]; then
            disk_error_flag=1
            out_string="$out_string read_err=$read_err"
        fi
        if [[ $write_err != 0 ]]; then
            disk_error_flag=1
            out_string="$out_string write_err=$write_err"
        fi
        if [[ $chk_sum_err != 0 ]]; then
            disk_error_flag=1
            out_string="$out_string chk_sum_err=$chk_sum_err"
        fi
        
        disk_err_array+=("$out_string")

done < <($zpool status | grep ONLINE | grep -v state)

if [ $disk_error_flag == 1 ]; then
    email_subject="$email_subject: disk errors detected"
    for item in ${disk_err_array[@]}; do
        echo "errors on: $item" | tee -a "$logfile"
    done
else
    echo "no silent errors seen for disks marked online in ZFS filesystem"
fi


echo -e "\ntesting multipath for errors"
if $multipath -ll &> /dev/null; then #check if multipath devices exist
        for mpath_device in $($multipath -ll | grep mpath | awk '{print $1}'); do
                if ! $multipath -ll $i | grep -v "active" &> /dev/null; then
                        mpath_error_flag=1
            email_subject="$email_subject: error found in multipath configuration"
                        echo "$i is unhealthy" | tee -a "$logfile"
                        $multipath -ll $i | tee -a "$logfile"
                fi
        done
    
    expected_num_of_mpath_devices=$($zpool status | grep mpath | wc -l)
    num_of_mpath_devices=$($multipath -ll | grep mpath | wc -l)
    
    if [ -z $expected_num_of_mpath_devices ]; then
        if [ $expected_num_of_mpath_devices != $num_of_mpath_devices ]; then
            mpath_error_flag=1
            echo "expected $expected_num_of_mpath_devices mpath devices, only $num_of_mpath_devices are seen" | tee -a "$logfile"
        
            echo "determining devices in /dev that are not defined in multipath, all devices other than sda are collected" | tee -a "$logfile"
            for i in $(cd /dev && ls sd* | grep -v "sda[123456]"); do 
                $multipath -ll | grep $i > /dev/null || echo -e "$i not found in multipath" | tee -a "$logfile"
            done
        fi
    fi
    
    
    
    if [ $mpath_error_flag == 0 ]; then
        echo "no errors found in multipath devices"
        echo "all $num_of_mpath_devices mpath devices defined for zpool accounted for"
    fi
else
    echo "multipath is not defined, nothing to do"
fi


#test percent usage for zpool
echo -e "\ntesting defined pools high watermarks and scrub intervals"
while read line; do
    zpool_name=$(echo $line | awk '{print $1}')
    capacity=$(echo $line | awk '{print $2}' | cut -d "%" -f 1)
    


    if $zpool status $zpool_name | egrep -c "scrub in progress|resilver" &> /dev/null; then
        echo "a scrub or resilver is in progress, will resume check after it's completion"
    else
        if $zpool status $zpool_name | egrep -c "none requested" &> /dev/null; then
            echo "a scrub has never been run, this check will monitor frequency after the first scrub of the pool"
        else
                        #last_scrub_date=$($zpool status $zpool_name | grep scrub | awk '{print $12 " " $13 " " $15}')
                        #last_scrub_secs=$(/bin/date -d "$last_scrub_date" +%s)
            last_scrub=$(/sbin/zdb -h $zpool_name | grep scrub | tail -1 | cut -d "." -f 1)
            if ! [ -z "$last_scrub" ]; then
                today_secs=$(/bin/date +%s)
                last_scrub_secs=$(/bin/date --date=$last_scrub +%s)
                sec_old=$(( $today_secs - $last_scrub_secs ))
                if [[ $sec_old -gt $scrubExpire ]]; then
                    echo "zpool $zpool_name has not been scrubbed in more than $scrub_days_old days" | tee -a "$logfile"
                else
                    echo "zpool $zpool_name has been scrubbed within the past ${scrub_days_old} day(s)."
                fi
            else
                echo "last_scrub is empty for $zpool_name, and shouldn't be" | tee -a "$logfile"
            fi
        fi
    fi
    
    if [[ $capacity -gt $zpool_capacity_limit ]]; then
        email_subject="$email_subject: $zpool_name exceeds high watermark"
        percent_use_flag=1
        echo "zpool $zpool_name is ${capacity}% full, exceeds high watermark set at ${zpool_capacity_limit}%" | tee -a "$logfile"
    else
        echo "zpool $zpool_name ${capacity}% full, which is within the limit set of ${zpool_capacity_limit}%"
    fi


done < <($zpool list -H -o name,capacity)


zfs_xinetd="/etc/xinetd.d/zfs"
zfs_recv_port=8023

# Check if xinetd is installed
if [[ "$protocol" == "xinetd" ]]; then
    echo -e "\nchecking to see if xinetd is installed"
    if ! rpm -qa | grep "xinetd" &> /dev/null; then
        email_subject="$email_subject: xinetd is not installed and is needed"
        error_flag=1
        echo "xinetd is not installed" | tee -a "$logfile"
    else
        echo "trying to restart xinetd"
        if ! sudo $service xinetd status &> /dev/null; then #after installation check if service is running and start it
                sudo $service xinetd restart
                check_previous "/sbin/service xinetd restart.  Restarting xinetd service has failed."
        else
            echo "successfully restarted xinetd"
        fi

        echo -e "\nchecking to see if $zfs_xinetd exists"
        if ! [ -e $zfs_xinetd ]; then
            echo "creating $zfs_xinetd"
                if [ $($zpool list -H -o name | wc -l) == 1 ]; then
                        zpool_name=$($zpool list -H -o name)

                        cat > $zfs_xinetd <<EOF
# default: off
# listening on $zfs_recv_port to stream snapshot over netcat
service zfs
{
                disable = no
                type                        = UNLISTED
                socket_type         = stream
                wait                        = no
                user                        = root
                server                  = /sbin/zfs
                server_args         = receive -F $zpool_name
                log_on_failure  += USERID
                port                        = $zfs_recv_port
                instances           = 1
}
EOF
                        logger -p info "added $zfs_xinetd listening on $zfs_recv_port for $zpool_name"
                        check_previous "logger -p info $zfs_xinetd"
                echo "reloading xinetd"
                        $service xinetd reload
                        check_previous "$service xinetd reload"
                else
                email_subject="$email_subject: cannot build xinetd configuration, more than one pool name returned"
                        error_flag=1
                        echo "returned more than one pool name, $zfs_xinetd will need to be built manually" | tee -a "$logfile"
                fi
        fi

        echo "checking to see if netstat is listening on $zfs_recv_port"
        if which netstat &> /dev/null; then
            if ! netstat -ap | grep 8023 | grep xinetd &> /dev/null; then
                email_subject="$email_subject: xinetd is not listening on $zfs_recv_port"
                    error_flag=1
                    echo "xinetd is not listening on $zfs_recv_port, cannot recieve snapshots" | tee -a "$logfile"
            else
                echo "netstat is listening on $zfs_recv_port"
            fi
        else
            echo "netstat does not exists, cannot test if zfs can recieve on $zfs_recv_port" | tee -a "$logfile"
        fi
    fi
fi

if [ -f "$logfile" ]; then
    if [ -s "$logfile" ]; then
        echo -e "\nerrors detected, sending contents to: $message_recipient"
        $mail_out -s "$email_subject" -r "$message_recipient" -m "$logfile"
        check_previous $mail_out -s "$email_subject" -r "$message_recipient" -m "$logfile"
        echo "removing logfile: $logfile"
        /bin/rm -f "$logfile"
        check_previous "rm -f $logfile"
        exit 1
    fi
else
    echo -e "\nall looks good"
fi
