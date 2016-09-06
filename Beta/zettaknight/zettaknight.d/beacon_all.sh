#!/bin/bash
#set -x

function check_previous () {
    ret_val=$?

    if [ "$ret_val" -ne 0 ]; then
        echo "${ret_val}: $@"
        exit 1
    fi
}

if [ "$1" == 'off' ]; then
    echo -e "\nturning off any illuminated beacons\n"
    ledctl locate_off=$(ls /dev/sd* | grep -v "/dev/sda[123456]" | awk 'BEING { OFS=","} { printf $1"," }')
    check_previous ledctl locate_off=$(ls /dev/sd* | grep -v "/dev/sda[123456]" | awk 'BEING { OFS=","} { printf $1"," }')
elif [ "$1" == 'on' ]; then
    search=$(ls /dev/disk/by-id/dm-uuid-mpath*)
else
    search=$@
fi
    
    
unset disk_array

for disk in $search; do
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

                #echo "$wwid: $mpath, $dm"

                for d in $devices; do
                    disk_array+=("/dev/${d}")
                    #ledctl failure="/dev/$d"check_previous ledctl failure="/dev/$d"
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
check_previous ledctl failure="$disk_string"
