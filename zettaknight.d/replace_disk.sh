#!/bin/bash
version="0.0.3"

#source helper functions
running_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
setopts="${running_dir}/setopts.sh"
source $setopts || { echo "failed to source $setopts"; exit 1; }

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
        echo "$?: $@"
        exit 1
    fi
}

function beacon_disk () {

    local disk="$1"

    if [ $# -ne 1 ]; then
        echo "function beacon_disk needs 1 argument: disk"
        exit 1
    fi
    
    #turn off beacons to start
    if which ledctl > /dev/null; then
		if [ $ledctl_reset_flag == 0 ]; then
        	echo -e "\nturning off any illuminated beacons"
        	ledctl locate_off=$(ls /dev/sd* | grep -v "/dev/sda[123456]" | awk 'BEING { OFS=","} { printf $1"," }')
        	check_previous ledctl locate_off=$(ls /dev/sd* | grep -v "/dev/sda[123456]" | awk 'BEING { OFS=","} { printf $1"," }')
			ledctl_reset_flag=1
		fi
    
    
        if ls /dev/ | grep "$disk" > /dev/null; then
            #beacon disk since it's already a raw device
            echo "raw device given, beaconing /dev/${disk}"
            ledctl failure=/dev/$disk
            check_previous ledctl failure=/dev/$disk
        fi
        
        #find dm device for device mapped in /dev/disk/by-id
        wwid=$(echo "$disk" | awk -F "-" '{print $NF}')
        if ! [ -z "$wwid" ]; then
            if ls /dev/disk/by-id | grep "$wwid" > /dev/null; then #if wwid is not empty
                disk_info=$(multipath -ll | grep "$wwid") #whole output to keep from running multipath over and over to determine variables
                mpath=$(echo "$disk_info" | awk '{print $1}') #mpathar etc
                dm=$(echo "$disk_info" | awk '{print $3}')
                disk_serial=$(sginfo -a /dev/mapper/${mpath} | awk '/Serial/ {print $NF}' | tr -d "'") #serial number of multipath device
                devices=$(multipath -ll $mpath | grep ":" | awk '{print $3}') #disks that make up the mpath devices
            
                echo -e "\n$disk, $mpath, $dm" 
                echo -e "\tserial: $disk_serial"

                
                echo -e "\nbeaconing $disk"
                   for d in $devices; do
                    smart_disk="$d" #this is used in smartctl since all paths are not needed
                       if ls /dev/ | grep "$d" > /dev/null; then #make sure determined devices are raw devices
                        ledctl failure=/dev/${d}
                        check_previous ledctl failure=/dev/${d}
                    else
                        echo "$d is not recognized in /dev/, cannot beacon"
                    fi
                done
            
            fi
        
            if which smartctl > /dev/null; then
                echo -e "\ngrabbing statistics for $disk"
                smartctl -H /dev/${smart_disk}
                check_previous "smartctl -x /dev/${smart_disk}"
            else
                echo "smartctl is needed for extended disk statistics"
            fi
        fi
    fi        
}


#options to be written in at a later date
setopts flag "-r|--run" "run_flag" "this option starts an automated replacement where a resilver is attempted for all failed disks"
setopts var "-d|--disk" "faulted_disk" "define a disk to be reslivered with the next available spare disk defined for the pool.\n\t Declaring -d will overwrite -r"


###############################################################################################
################## create zpool array definition ##############################################
###############################################################################################
#create array of all zpools
unset zpool_array
for zpool in $(zpool list -o name -H); do
    zpool_array+=("$zpool") #zpool_array is an array that contains all zpools defined on the system
done

if [ ${#zpool_array[@]} == 0 ]; then #if the are no items in this array, exit
    echo -e "\nthere are no zpools defined, there is nothing for this script to do"
    exit 0
fi
###############################################################################################
###############################################################################################
###############################################################################################



for zpool in ${zpool_array[@]}; do #read in the list of all zpools
    if zpool status $zpool | grep "FAULTED" > /dev/null; then


        ###############################################################################################
        ############################ build faulted drive array ########################################
        ###############################################################################################
        #test if FAULTED item is a disk
        unset faulted_disk_array
		ledctl_reset_flag=0 #this flag is used in the function beacon_disk to make sure ledctl is only reset 1 time, not each consecutive time it's called, resetting what it's set
        for faulted_disk in $(zpool status $zpool | grep "FAULTED" | awk '{print $1}' | grep -v "raidz" | grep -v "spare"); do #awk out the name of the item
            faulted_disk_array+=("$faulted_disk") #confirmed as a disk, add to array for replacement
			beacon_disk $faulted_disk
        done
    
        if [ ${#faulted_disk_array[@]} == 0 ]; then #if the are no items in this array, exit
            echo -e "\nfaulted items exist in the pool, but are not disk items, there is nothing this script can do"
            exit 1
        fi
    
        echo -e "\ndisk(s) currently in a faulted state: ${faulted_disk_array[@]}"
        ###############################################################################################
        ###############################################################################################
        ###############################################################################################



        ###############################################################################################
        #### calculate the number of lines needed to tail out the spare definition in zpool status ####
        ###############################################################################################
        if ! zpool status $zpool | grep "spares" > /dev/null; then
            echo "there are no spares defined for zpool $zpool, faulted disks cannot be replaced"
            exit 1
        fi
        total_lines=$(zpool status $zpool | wc -l)
        spares_line_num=$(zpool status $zpool | /bin/grep -n "spares" | cut -d ":" -f1) #line number in zpool status where the spares definition starts
        num_lines_tail=$(( $total_lines - $spares_line_num ))
        ###############################################################################################
        ###############################################################################################
        ###############################################################################################
 
 
 
        ###############################################################################################
        ############################ build spare array ################################################
        ###############################################################################################        
        unset spare_disk_array
        echo -e "\nchecking system for available spares:"
        for spare_disk in $(zpool status $zpool | tail -n $(( $num_lines_tail )) | awk '{print $1}'); do
            if [ -e /dev/${spare_disk} ] || [ -e /dev/mapper/${spare_disk} ] || [ -e /dev/disk/by-id/${spare_disk} ]; then
                if zpool status $zpool | grep "$spare_disk" | grep "AVAIL" &> /dev/null; then
                    echo "AVAIL: $spare_disk"
                    spare_disk_array+=("$spare_disk")
                else
                    echo "UNAVAIL: $spare_disk"
                fi
            fi
        done
        
        if [ ${#spare_disk_array[@]} == 0 ]; then #if the are no items in this array, exit
            echo "there are no spare disks to resilver data, script must exit"
            exit 1
        fi
        ###############################################################################################
        ###############################################################################################
        ###############################################################################################        


        ###############################################################################################
        ########################### find ashift value for the zpool ###################################
        ###############################################################################################
        ashift=$(zpool get -H ashift $zpool | awk '{print $3}')
        echo -e "\ndetermined ashift value for $zpool is $ashift"
        ###############################################################################################
        ###############################################################################################
        ###############################################################################################



        ###############################################################################################
        ############################# replace disk with a spare #######################################
        ###############################################################################################
        #replace disk with an AVAIL spare not in use
        faulted_disk_index=0
        spare_disk_index=0
        is_spare_flag=0
        
        echo -e "\nstarting disk replacement"
        for faulted_disk in ${faulted_disk_array[@]}; do
            for spare_disk in ${spare_disk_array[@]}; do
                if [ "$faulted_disk" == "$spare_disk" ]; then #check if faulted disk is a spare, if so, do not replace, only warn
                    is_spare_flag=1
                    echo "faulted disk: $faulted_disk is in the spare pool, will not be replaced"
                    faulted_disk_index=$(( $faulted_disk_index + 1 ))
                fi
            done
            
            if [ $is_spare_flag == 0 ]; then #if disk needing replacement is not a spare
                if zpool status $zpool | grep -A 1  "${faulted_disk_array[$faulted_disk_index]}" | grep "resilvering" > /dev/null; then 
                    echo "${faulted_disk_array[$faulted_disk_index]} is already being resilvered"
                    faulted_disk_index=$(( $faulted_disk_index + 1 ))
                else
                    if ! [ -z ${spare_disk_array[$spare_disk_index]} ]; then
                        echo -e  "\nreplacing disk ${faulted_disk_array[$faulted_disk_index]} with spare ${spare_disk_array[$spare_disk_index]}"
                        zpool replace -o ashift=9 $zpool ${faulted_disk_array[$faulted_disk_index]} ${spare_disk_array[$spare_disk_index]}
                        ret_val=$?
                        if [ $ret_val != 0 ]; then
                            echo "failed to replace disk ${faulted_disk_array[$faulted_disk_index]} with spare ${spare_disk_array[$spare_disk_index]}"
                            echo "exiting due to error"
                            exit $ret_val
                        else
                            echo "replace of ${faulted_disk_array[$faulted_disk_index]} issued successfully"
                        fi
                    else
                        echo -e "**** insufficient spares for the number of faulted drives, cannot continue ****"
                        exit 1
                    fi
                fi
                
                faulted_disk_index=$(( $faulted_disk_index + 1 )) #interate the next available disk and spare in the array
                spare_disk_index=$(( $spare_disk_index + 1 )) #if 
            fi
            
            #echo "$faulted_disk_index disk"
            #echo "$spare_disk_index spare"
            
            is_spare_flag=0 #reset spare flag for next loop
        done
        ###############################################################################################
        ###############################################################################################
        ###############################################################################################        
        
        
    else
        echo "no faulted disks seen, nothing to do"
        exit 0
    fi
done