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

read_flag=0
write_flag=0
delete_flag=0
create_flag=0

###################################################################
##################do not edit anything below this line#############
###################################################################

function clean_up () {
        #remove dummy files after records have been recorded
        cd
    if [ -e "$diskperf_test_location" ]; then
        echo "removing $diskperf_test_location"
        ${rm_path} -rf "${diskperf_test_location}"
        if [ $? -ne 0 ]; then
            echo "$? : {rm_path} -rf ${diskperf_test_location}"
            echo "$diskperf_test_location will need to be removed manually"
        fi
    fi
}

function check_previous () {
        if [ $? -ne 0 ]; then
                echo $@
        clean_up
                exit 1
        fi
}

function check_if_integer () {
        local var=$1
        if ! [[ $var =~ ^[-+]?[0-9]+$ ]]; then #test if input is an integer
        echo "$var is not an integer"
            show_help
            exit 1
        fi
}

#function unmount_filesystem () {
        #unmount filessystem before read
        #testLocationNoSlash=$( echo $test_location | cut -d "/" -f 2)
        #cd
        #sudo zfs umount "$testLocationNoSlash"
        #check_previous "failed to umount $testLocationNoSlash"
        #sudo zfs mount "$testLocationNoSlash"
        #check_previous "failed to mount $testLocationNoSlash"
        #d $diskperf_test_location
        #heck_previous "failed to cd into $diskperf_test_location"
#}

function install_diskperf () {
    download_loc="/tmp/${date_format}_diskperf_install_script"

    echo "if $0 can pull from svn, diskperf can be downloaded for you"
    echo "a directory in tmp will be created and diskperf will be added to /usr/bin"
    read -p "install? [y/n]: " -r 
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        mkdir -p $download_loc
        check_previous "mkdir -p $download_loc"
        echo "created $download_loc"
        cd $download_loc
        check_previous "cd $download_loc"
        svn checkout svn://svn.code.sf.net/p/diskperf/code/trunk diskperf-code
        check_previous "svn checkout svn://svn.code.sf.net/p/diskperf/code/trunk diskperf-code"
        cd ${download_loc}/diskperf-code/ && make
        check_previous "cd ${download_loc}/diskperf-code/ && make"
        mv ${download_loc}/diskperf-code/diskperf /usr/bin/
        check_previous "mv ${download_loc}/diskperf-code/diskperf /usr/bin/"
        if [ -e "$download_loc" ]; then
            rm -rf "$download_loc"
            check_previous "rm -rf $download_loc"
            echo "removed $download_loc"
        fi
    else
        echo "user does not want to continue"
        exit 1
    fi
    }

function show_help () {
    echo -e "\n-b block size"
    echo "-p processes"
    echo "-w write"
    echo "-r read"
    echo "-f output File size"
    echo "-d delete files after complete"
    echo "-l location to mount"
    echo "-c test file creation rates"
}

while getopts "b:c:p:w:f:l:r:d?" OPTION
do
     case $OPTION in
        b) 
            diskperf_buffer=$OPTARG
            ;;
        c) 
            create_flag=1
            write_flag=1
            ;;
        p)
            diskperf_process=$OPTARG
            check_if_integer $diskperf_process
            ;;
        w)
            write_flag=1
            diskperf_write=$OPTARG
            diskperfNum=$diskperf_write
            check_if_integer $write_flag
            ;;
        f)
            diskperf_file_size=$OPTARG
            check_if_integer $diskperf_file_size
            ;;
        l)
            test_location=$OPTARG
            ;;
        r)
            read_flag=1
            diskperfRead=$OPTARG
            check_if_integer $read_flag
            diskperfNum=$diskperfRead
            ;;
        d)
            delete_flag=1
            ;;
        :)
            show_help
            exit 1
            ;;
        help)
            show_help
            exit 1
            ;;
    esac
done

########## globals #########################
############################################

date_format=$(date '+%Y%m%d')
date_format2=$(date '+%Y%m%d_%H:%M:%S')
rm_path="/bin/rm"
iozone_path="/usr/bin/iozone"
diskperf_path=$(which diskperf)
if [ -z $diskperf_path ] || [ ! -x $diskperf_path ]; then
    echo "diskperf does not exist"
    install_diskperf #function will exit if user chooses not to continue at prompt
    diskperf_path=$(which diskperf) #diskperf_path did not yet exist, set after diskperf is created
fi


############## script start #################
#############################################

#trap ctrl+c so clean_up function is run on ctrl+c
trap "{ echo ctrl+c : interrupt; clean_up; }" INT

if [[ -z "$diskperf_buffer" || -z "$diskperf_process" || -z "$diskperf_file_size" || ! -e "$test_location" ]]; then
    if [ $create_flag == 0 ]; then
        echo "missing required arguments"
        echo "-b=$diskperf_buffer"
        echo "-p=$diskperf_process"
        echo "-f=$diskperf_file_size"
        echo "-l=$test_location"
        show_help
        exit 1
    fi
fi

if [ $create_flag == 1 ] && [ $read_flag == 1 ]; then
    echo "-r (read test) cannot be specified with -c (file creation test)"
    show_help
    exit 1
fi

if [ $create_flag == 1 ]; then
    diskperf_buffer=1k
    diskperf_process=4
    diskperf_count=0
    diskperf_write=250000
else
    d0=$(echo $diskperf_buffer | sed 's/[^0-9]*//g')
    d1=$((${diskperf_file_size} * 1048576))
    d2=$((${d1} / ${d0}))
    d3=$((${d2} / ${diskperf_process}))
    d4=$((${d3} / ${diskperfNum}))
    diskperf_count=${d4}
fi

if [ $write_flag == 0 ] && [ $read_flag == 0 ]; then
    echo "either -r or -w is required"
    show_help
    exit 1
fi

string="$test_location"
case $string in
        */) ;;
        *) test_location="${test_location}/";;
esac
        diskperf_test_location="${test_location}${date_format}_script_junk_files/"

#test to run
if [ $write_flag == 1 ]; then
    mkdir -p $diskperf_test_location
    check_previous "failed to create $diskperf_test_location"
    cd $diskperf_test_location
    check_previous "failed to cd to $diskperf_test_location"

#    if [ $iops_flag == 1 ]; then
#        cd $diskperf_test_location
#        check_previous "failed to cd to $diskperf_test_location"
#        echo -e "\ndiskperf -c ${diskperf_count} -b ${diskperf_buffer} -p ${diskperf_process} -w ${diskperfNum}"
#        s0=$({ /usr/bin/time -f '%e' ${diskperf_path} -c ${diskperf_count} -b $diskperf_buffer -p ${diskperf_process} -w ${diskperfNum} | grep "Aggregate"; } 2>&1)
#
#        c0="$(echo $s0 | cut -d " " -f 1)"
#        c1="$(echo $s0 | cut -d ":" -f 2)"
#        s1=$(echo "scale=5; ${diskperf_process} * ${diskperfNum}" | bc)
#        s2=$(echo "scale=2; ${s1} / ${c0}" | bc)
#        echo "Throughput: $c1"
#        echo "IOPS: $s2"
#    else
        echo -e "\ndiskperf -c ${diskperf_count} -b ${diskperf_buffer} -p ${diskperf_process} -w ${diskperf_write}"
        ${diskperf_path} -c ${diskperf_count} -b ${diskperf_buffer} -p ${diskperf_process} -w ${diskperf_write} | grep "Aggregate"
        check_previous "failed to execute $diskperf_path"
#    fi
fi

if [ $read_flag == 1 ]; then
    if ! [ -e $diskperf_test_location ]; then
        echo "$diskperf_test_location does not exist"
        exit 1
    fi
        cd $diskperf_test_location
        check_previous "failed to cd to $diskperf_test_location"
        echo -e "\ndiskperf -c ${diskperf_count} -b ${diskperf_buffer} -p ${diskperf_process} -r ${diskperfRead}"
        ${diskperf_path} -c ${diskperf_count} -b ${diskperf_buffer} -p ${diskperf_process} -r ${diskperfRead} | grep "Aggregate"
fi

if [ $delete_flag == 1 ]; then
    clean_up
fi
