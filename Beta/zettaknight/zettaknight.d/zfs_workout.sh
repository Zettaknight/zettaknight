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

version="1.1"

#source helper functions
running_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
setopts="${running_dir}/setopts.sh"
zfs_zpool_create="${running_dir}/zfs_zpool_create.sh"
zfs_nuke="${running_dir}/zfs_nuke.sh"
diskperf="${running_dir}/diskperf_one_run.sh"

source $setopts || { echo "failed to source $setopts"; exit 1; }

#exit on error
set -e

function delete_zpool () {
    $zfs_nuke -p $zpool_name -f > /dev/null
}

function test_zpool () {
    local data_disks=$1
    local raidz=$2

    if [ $# -ne 2 ]; then
        echo "function 'test_zpool' did not recieve required arguments"
        exit 1
    fi

    #create the zpool
    $zfs_zpool_create -p $zpool_name -f $disk_list -d $data_disks -z $raidz > /dev/null

    #gather info about the zpool
    usable_space=$(zfs get available -o value -H)
    total_space=$(zpool list | grep $zpool_name | awk '{print $2}')
    parity_space=$(( $(echo "$total_space" | sed 's/[^0-9]*//g') - $(echo "$usable_space" | sed 's/[^0-9]*//g') ))
    num_disks_vol=$(( $data_disks + $raidz ))
    vol_str="${data_disks}+${raidz}"
    if [ $raidz == 4 ]; then
        num_disks_vol=$(( $data_disks + $data_disks ))
        vol_str="${data_disks}+${data_disks}"
        parity_space=$(( ($parity_space * 2) + $(echo "$usable_space" | sed 's/[^0-9]*//g') ))
    fi
    num_vols=$(( $total_disks / $num_disks_vol ))
    total_num_data_disks=$(( (${total_disks}/${num_disks_vol}) * $data_disks ))
    spares=$(( $total_disks - $total_num_data_disks )) #duh, remainder, not datadisks
    remainder=$(($total_disks % $num_disks_vol))
    total_disk_in_pool=$(($total_disks - $remainder))
    spares=$(( $total_disks - $total_disk_in_pool ))

    #test zpool, parse output
    echo -e "\n${num_vols}x(${vol_str}) : ${d_file_size} file in $d_buffer buffer over $d_process process(es)"
    echo "available_space: $usable_space ("" + $parity_space""T overhead)"
    echo "spares: $spares"

    sleep 10
    
    #convert bytes to gigabytes for diskperf_one_run.sh function, need to change implementation so conversion is not necessary
    file_size_gb=$( echo "$file_size_int / 1024 / 1024 / 1024" | bc )
    
    diskperf_out=$($diskperf -b "$d_buffer" -f "$file_size_gb" -l "/${zpool_name}" -p "$d_process" -w 1 -d)
    speed=$(echo "$diskperf_out" | grep Aggregate | cut -d " " -f 4)
    
    echo "throughput: $speed MB/s"
    speed_per_disk=$(echo "${speed}/${total_num_data_disks}" | bc )
    echo "speed/data_disk: $speed_per_disk MB/s"

    if [ $create_flag == 1 ]; then
        tx=$($diskperf -c -l "/${zpool_name}" -d | grep "Aggregate" | cut -d " " -f 9)
        creates=$(echo "$tx / 2" | bc)
        echo "File creations (1,000,000 files): $creates /sec"
    fi

    delete_zpool
}

function show_help () {
cat <<EOF

version $version

USAGE:
$0 [sbfpwc]

DESCRIPTION:
    $(basename $0) is used to test a ZFS filesystem in multiple configurations to determine the
    best performance model.  A ZFS filesystem , named -p <name>, will be createdfor a list of -f disks
    (file \n delimeted), performance tested with diskperf.  The pool will then be destroyed and a new
    configuration will be tested.

OPTIONS:
REQUIRED:
    -f list of disks from a file separated by \n
    -s file size (in GBs) to be tested
    -p number of processes to spawn for diskperf
    -b block size for each diskperf test
    -w number of files to create
OPTIONAL:
    -c also performs a -w <value> file creation test
    -z raidz level
        0. stripe
        1. raidz1
        2. raidz2
        3. raidz3
        4. mirror

EOF

exit 1 #exit after being helpful
}

create_flag=0
raid="0 1 2 3 4"

while getopts "s:b:f:p:w:z::c?" OPTION
do
        case $OPTION in
                s)
                        d_file_size=$OPTARG
                        ;;
                b)
                        d_buffer=$OPTARG
                        ;;
                f)
                        disk_list=$OPTARG
                        ;;
                p)
                        d_process=$OPTARG
                        ;;
                w)
                        d_write=$OPTARG
                        ;;
                c)
                        create_flag=1
                        ;;
                z)
                        raid=$OPTARG
                        ;;
                :)
                        show_help
                        ;;
                help)
                        show_help
                        ;;
        esac
done

if [ -z "$d_file_size" ] || [ -z "$d_buffer" ] || [ -z "$disk_list" ] || [ -z "$d_process" ]; then
    echo -e "\nrequired arguments missing\n"
    show_help
    exit 1
fi


zpool_name="generic_test_pool_name"
total_disks=$(cat $disk_list | wc -l)


file_size_int=$( echo "$d_file_size" | tr -d "[A-Z][a-z]" ) #remove any non-interger
file_size_suffix=$( echo "$d_file_size" | tr -d "[0-9]" ) #MB GB KB or TB

if [ "$file_size_suffix" == "KB" ] || [ "$file_size_suffix" == "k" ] || [ "$file_size_suffix" == "K" ]; then
    file_size_int=$( echo "$file_size_int * 1024" | bc )
elif [ "$file_size_suffix" == "MB" ] || [ "$file_size_suffix" == "m" ] || [ "$file_size_suffix" == "M" ]; then
    file_size_int=$( echo "$file_size_int * 1024 * 1024" | bc )
elif [ "$file_size_suffix" == "GB" ] || [ "$file_size_suffix" == "g" ] || [ "$file_size_suffix" == "G" ]; then
    file_size_int=$( echo "$file_size_int * 1024 * 1024 * 1024" | bc )
elif [ "$file_size_suffix" == "TB" ] || [ "$file_size_suffix" == "t" ] || [ "$file_size_suffix" == "T" ]; then
    file_size_int=$( echo "$file_size_int * 1024 * 1024 * 1024 * 1024" | bc)
else
    echo "acceptable arguments for file size are KB[K][k] MB[M][m] GB[G][g] or TB[T][t], exiting"
    show_help
    exit 1
fi


trap "{ echo ctrl+c : interrupt; delete_zpool; }" INT

for raidz in $raid; do
    if [ $raidz == 0 ]; then #test the full stripe
        data_disks=$total_disks
        test_zpool $data_disks $raidz
    fi

    if [ $raidz == 1 ]; then
        for value in $(seq 5 20); do
            data_disks=$value
            test_zpool $data_disks $raidz
        done
    fi

    if [ $raidz == 2 ]; then
        for value in $(seq 5 20); do
            data_disks=$value
            test_zpool $data_disks $raidz
        done
    fi

    if [ $raidz == 4 ]; then
        data_disks=1
        test_zpool $data_disks $raidz
    fi
done
