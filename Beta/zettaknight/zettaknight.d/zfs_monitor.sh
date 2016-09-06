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
version="0.0.21"

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



############## check if root ########################

if [ $(id -u) != 0 ]; then #check if ran as root user

    echo "$0 needs to be ran as root" | tee -a "$logfile"
    error_flag=1
    $mail_out "$(hostname) : must be ran as root $0"
    exit 1
    
fi

#####################################################


############## test pool health #####################

echo -e "\ntesting health of the zpool"

for pool in $($zpool list -o name -H); do

    if $zpool status "$pool" -x | grep -v "pool '$pool' is healthy" &> /dev/null; then
    
        error_flag=1
        email_subject="$email_subject: zpool is not healthy"
        $zpool status "$pool" -x | tee -a "$logfile"
        
    else
    
        echo "zpool $pool is healthy"
        
    fi
    
    echo -e "\nchecking to see if any disks are in a failed status, if spares are defined a resilver will be started"
    
    
    if $zpool status $pool | grep "FAULTED" > /dev/null; then
    
        unset faulted_disk_array
        for faulted_disk in $($zpool status $pool | grep "FAULTED" | awk '{print $1}' | grep -v "raidz" | grep -v "spare"); do #awk out the name of the item
        
            faulted_disk_array+=("$faulted_disk") #confirmed as a disk, add to array for replacement
            
        done
    
        if [ ${#faulted_disk_array[@]} != 0 ]; then #if the are items in this array
        
            #beacon faulted disks
            if which ledctl &> /dev/null; then
            
                unset disk_array
            
                for disk in ${faulted_disk_array[@]}; do
                
                    if ! [ -z "$disk" ]; then
                    
                        if ls /dev | grep "$disk" > /dev/null; then
                        
                            disk_array+=("/dev/${disk}")
                            
                        else
                        
                            wwid=$(echo "$disk" | awk -F "-" '{print $NF}')
                            
                            if ls /dev/disk/by-id | grep "$wwid" > /dev/null; then #if wwid is not empty
                            
                                disk_info=$(multipath -ll | grep "$wwid") #whole output to keep from running multipath over and over to determine variables
                                mpath=$(echo "$disk_info" | awk '{print $1}') #mpathar etc
                                dm=$(echo "$disk_info" | awk '{print $3}')
                                devices=$(multipath -ll $mpath | grep ":" | awk '{print $3}') #disks that make up the mpath devices

                                for d in $devices; do
                                
                                    disk_array+=("/dev/${d}")
                                    
                                done

                            fi

                        fi
                    fi

                done
            
                for disk in ${disk_array[@]}; do
                
                    if [ -z "$disk_string" ]; then
                    
                        disk_string="$disk"
                        
                    else
                    
                        disk_string="${disk_string},${disk}"
                        
                    fi
                    
                done

                echo -e "running:\nledctl failure=$disk_string"
                ledctl failure="$disk_string"
                
            fi
            #### end beacon disks ####
        
            if $zpool status $pool | grep "spares" > /dev/null; then
            
                total_lines=$($zpool status $pool | wc -l)
                spares_line_num=$($zpool status $pool | /bin/grep -n "spares" | cut -d ":" -f1) #line number in zpool status where the spares definition starts
                num_lines_tail=$(( $total_lines - $spares_line_num ))
                
                unset spare_disk_array
                unset inuse_spare_array
                echo -e "\nSpares exist, checking for availability:"
                
                for spare_disk in $($zpool status $pool | tail -n $(( $num_lines_tail )) | awk '{print $1}'); do
                
                    if [ -e /dev/${spare_disk} ] || [ -e /dev/mapper/${spare_disk} ] || [ -e /dev/disk/by-id/${spare_disk} ]; then
                    
                        if $zpool status $pool | grep "$spare_disk" | grep "AVAIL" &> /dev/null; then
                        
                            echo "AVAIL: $spare_disk"
                            spare_disk_array+=("$spare_disk")
                            
                        elif $zpool status $pool | grep "$spare_disk" | grep "INUSE" &> /dev/null; then
                            echo "INUSE: $spare_disk"
                            inuse_spare_array+=("$spare_disk")
                            
                        else
                        
                            echo "UNAVAIL: $spare_disk"
                            
                        fi
                    fi
                done
                
                if [ ${#spare_disk_array[@]} != 0 ]; then #if the are no items in this array
                
                
                    #determine ashift value for the zpool
                    ashift=$($zpool get -H ashift $pool | awk '{print $3}')
                    echo -e "\ndetermined ashift value for $pool is $ashift"
                    
                    
                    #replace disk with an AVAIL spare not in use
                    faulted_disk_index=0
                    spare_disk_index=0
                    is_spare_flag=0
        
                    echo -e "\nstarting disk replacement"
                    for faulted_disk in ${faulted_disk_array[@]}; do
                    
                        for spare_disk in ${spare_disk_array[@]}; do
                        
                            is_spare_flag=0 #reset is_spare_flag
                            
                            if [ "$faulted_disk" == "$spare_disk" ]; then #check if faulted disk is a spare, if so, do not replace, only warn
                            
                                is_spare_flag=1
                                echo "faulted disk: $faulted_disk is in the spare pool, will not be replaced"
                                faulted_disk_index=$(( $faulted_disk_index + 1 ))
                            fi
                            
                        done
            
                        if [ $is_spare_flag == 0 ]; then #if disk needing replacement is not a spare
                        
                            next_disk=$($zpool status $pool | grep -A 1  "${faulted_disk_array[$faulted_disk_index]}" | awk '{print $1}' | tail -1)
                            
                            if ! [ -z "$next_disk" ]; then
                            
                                is_inuse_flag=0
                                
                                for blah in ${inuse_spare_array[@]}; do
                                
                                    if [ "$blah" == "$next_disk" ]; then
                                    
                                        echo "${faulted_disk_array[$faulted_disk_index]} is already being resilvered"
                                        faulted_disk_index=$(( $faulted_disk_index + 1 ))
                                        is_inuse_flag=1
                                        
                                    fi
                                    
                                done
                                
                                if [[ "$is_inuse_flag" == 0 ]]; then #if faulted disk does not have a an in use spare assigned to it
                                
                                    if ! [ -z ${spare_disk_array[$spare_disk_index]} ]; then #if there is a spare
                                    
                                        echo -e  "\nreplacing disk ${faulted_disk_array[$faulted_disk_index]} with spare ${spare_disk_array[$spare_disk_index]}"
                                        $replace_disk -a $ashift -p $pool -d ${faulted_disk_array[$faulted_disk_index]} -s ${spare_disk_array[$spare_disk_index]} | tee -a "$logfile"
                                        
                                    else
                                    
                                        echo -e "**** NO SPARES AVAILABLE : ${faulted_disk_array[$faulted_disk_index]} will NOT BE REPLACED ****"
                                        
                                    fi
                                fi
                
                                faulted_disk_index=$(( $faulted_disk_index + 1 )) #interate the next available disk and spare in the array
                                spare_disk_index=$(( $spare_disk_index + 1 )) #if 
                            else
                                echo "Cannot determine replacement status for [${faulted_disk}]"
                            fi
                        fi
                        #echo "$faulted_disk_index disk"
                        #echo "$spare_disk_index spare"
            
                        is_spare_flag=0 #reset spare flag for next loop
                    done
                
                else
                
                    echo "spares defined for $pool are not available to resilver data" | tee -a $logfile
                    
                fi
            
            else
            
                echo "there are no spares defined for zpool $pool, faulted disks cannot be replaced" | tee -a $logfile
                
            fi
        
        else
        
            echo -e "\nfaulted items exist in the pool, but are not disk items, there is nothing this script can do" | tee -a $logfile
            
        fi
    fi
    
    ############## check for silent pool errors ##########

    #check for disk errors
    echo -e "\nchecking for errors on disks currently ONLINE for $pool"
    #disk_err_array=()

    while read line; do
    
            scrub_flag=0 #if tripped, run a scrub of the pool

            disk=$(echo "$line" | awk '{print $1}')
            read_err=$(echo "$line" | awk '{print $3}')
            write_err=$(echo "$line" | awk '{print $4}')
            chk_sum_err=$(echo "$line" | awk '{print $5}')
            
            if [[ $read_err != 0 ]] || [[ $write_err != 0 ]] || [[ $chk_sum_err != 0 ]]; then
            
                disk_error_flag=1
                echo -e "errors detected on ${disk}:\n\t${line}" | tee -a "$logfile"
                #disk_err_array+=("$disk")
                
                
                if $zpool status $zpool_name | egrep -c "scrub in progress|resilver" &> /dev/null; then
                
                    echo -e "\na scrub or resliver is in progress, error correction will resume after completion"
                
                else
                
                    if [[ "$pool" == "$disk" ]]; then #if you're clearing errors from the zpool itself
                
                        $zpool clear $pool
                        echo -e "errors cleared on $disk\n" | tee -a $logfile
                        scrub_flag=1
                
                    else
                            
                        $zpool clear $pool $disk
                        echo -e "errors cleared on $disk\n" | tee -a $logfile
                        scrub_flag=1
                
                    fi
                fi
            fi
    
    done < <($zpool status | grep ONLINE | grep -v state)

    if [ $disk_error_flag == 1 ]; then

        email_subject="$email_subject: disk errors detected"
        
    else

        echo "no silent errors seen for disks marked online in ZFS filesystem"
        
    fi
    
    #start a scrub if errors are cleared
    if [[ $scrub_flag == 1 ]]; then
    
        echo -e "due to errors on disks, a scrub will be started for $pool:" | tee -a $logfile
        $zpool scrub $pool | tee -a $logfile
        
    fi 
      
done

#####################################################

######################################################

############ test percent usage for zpool ###########

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
        
            last_scrub_date=$($zpool status $zpool_name | grep scrub | awk '{print $12 " " $13 " " $15}')
            last_scrub_secs=$(/bin/date -d "$last_scrub_date" +%s)
            today_secs=$(/bin/date +%s)
            sec_old=$(( $today_secs - $last_scrub_secs ))
            
            if [[ $sec_old -gt $scrubExpire ]]; then
            
                echo "zpool $zpool_name has not been scrubbed in more than $scrub_days_old days" | tee -a "$logfile"
                
            else
            
                echo "zpool $zpool_name has been scrubbed within the past ${scrub_days_old} day(s)."
                
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
    
#####################################################




if [ -f "$logfile" ]; then

    if [ -s "$logfile" ]; then
    
        echo -e "\nerrors detected, sending contents to: $message_recipient"
        $mail_out -s "$email_subject" -r "$message_recipient" -m "$logfile"
        check_previous $mail_out -s "$email_subject" -r "$message_recipient" -m "$logfile"
        echo "removing logfile: $logfile"
        /bin/rm -f "$logfile"
        check_previous "rm -f $logfile"
        
    fi
    
else

    echo -e "\nall looks good"
    
fi
