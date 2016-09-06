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

#needs bc

running_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
setopts="${running_dir}/setopts.sh"
source $setopts || { echo "failed to source $setopts"; exit 1; }
pwd="$(pwd)"

date_time=$(date +'%Y%m%d')
test_file="${date_time}_test_file"
scp="/usr/bin/scp"

function check_previous () {
    if [ $? -ne 0 ]; then
        echo -e "\n$?: $@\n" | tee -a "$logfile"
        exit 1
    fi
}

setopts var "-f|--file_size" "file_size" "test file size: eg. 10MB (Mega) or 10M (Mibbi)"
setopts var "-r|--remote_ssh" "remote_ssh" "credentials for remote server i.e <user>@<hostname>"
setopts var "-b|--block_size" "block_size" "block size"
setopts var "-n|--port_num" "port_num" "port number for ssh"
setopts var "-c|--cipher" "cipher" "cipher to use for ssh"
setopts var "-s|--scp" "scp" "alternate path for scp [default: $scp], enter it here ex. [/usr/local/bin/scp]"
setopts var "-d|--remote_dir" "remote_dir" "remote location to write file"

if [[ -z "$file_size" ]] || [[ -z "$block_size" ]] || [[ -z "$scp" ]]; then
    show_help
    exit 1
fi 

if [[ -z "$port_num" ]]; then
    port_num=22
fi

if [[ ! -z "$remote_ssh" ]]; then
    if [[ -z "$remote_dir" ]]; then
        echo "remote_dir is necessary when remote_ssh is specified"
        show_help
        exit 1
    fi
fi

if [[ ! -x "$scp" ]]; then
    echo -e "\ncan't use $scp, cannot execute\n"
    show_help
    exit 1
fi

#calculate block size and count to match file size
file_size_int=$( echo "$file_size" | tr -d "[A-Z][a-z]" ) #remove any non-interger
file_size_suffix=$( echo "$file_size" | tr -d "[0-9]" ) #MB GB KB or TB

if [ "$file_size_suffix" == "KB" ] || [ "$file_size_suffix" == "k" ] || [ "$file_size_suffix" == "K" ]; then
    file_size_int=$( echo "$file_size_int * 1000" | bc )
elif [ "$file_size_suffix" == "MB" ] || [ "$file_size_suffix" == "m" ] || [ "$file_size_suffix" == "M" ]; then
    file_size_int=$( echo "$file_size_int * 1000 * 1000" | bc )
elif [ "$file_size_suffix" == "GB" ] || [ "$file_size_suffix" == "g" ] || [ "$file_size_suffix" == "G" ]; then
    file_size_int=$( echo "$file_size_int * 1000 * 1000 * 1000" | bc )
elif [ "$file_size_suffix" == "TB" ] || [ "$file_size_suffix" == "t" ] || [ "$file_size_suffix" == "T" ]; then
    file_size_int=$( echo "$file_size_int * 1000 * 1000 * 1000 * 1000" | bc)
else
    echo "acceptable arguments for file size are KB MB GB or TB, exiting"
    show_help
    exit 1
fi

#echo "$file_size converted to: $file_size_int bytes"

#determine block size in bytes
block_size_int=$( echo "$block_size" | tr -d "[A-Z][a-z]" )
block_size_suffix=$( echo "$block_size" | tr -d "[0-9]" )

if [ "$block_size_suffix" == "KB" ] || [ "$block_size_suffix" == "k" ] || [ "$block_size_suffix" == "K" ]; then
    block_size_int=$( echo "$block_size_int * 1024" | bc )
elif [ "$block_size_suffix" == "MB" ] || [ "$block_size_suffix" == "m" ] || [ "$block_size_suffix" == "M" ]; then
    block_size_int=$( echo "$block_size_int * 1024 * 1024" | bc )
else
    echo "acceptable arguments for block size are KB and MB, exiting"
    show_help
    exit 1
fi

#echo "$block_size coverted to: $block_size_int bytes"

dd_count=$( echo "$file_size_int / $block_size_int" | bc ) #file size in bytes divided by block size in bytes to determine count

#test 1
#dd if=/dev/zero of=${test_file} bs=${block_size_int} count=${dd_count}
#check_previous "failed to create test file"

#test 2, sync the entire file dd has written one time before returning
echo -e "\ndd if=/dev/zero of=${test_file} bs=${block_size_int} count=${dd_count} conv=fdatasync"
echo "writing file to ${pwd}/${test_file}"
dd if=/dev/zero of="${pwd}/${test_file}" bs=${block_size_int} count=${dd_count} conv=fdatasync
check_previous "dd if=/dev/zero of="${pwd}/${test_file}" bs=${block_size_int} count=${dd_count} conv=fdatasync"

#test 3 each write is commited to disk before returning, write cache is basically unused
#dd if=/dev/zero of=${test_file} bs=${block_size_int} count=${dd_count} oflag=dsync
#check_previous "failed to create test file"

du -h $test_file

if ! [ -z "$remote_ssh" ]; then
    echo -e "\ntesting default ssh tunnel: $remote_ssh"
    if [[ -z "$cipher" ]]; then
        down_speed=$($scp -v -P $port_num $test_file ${remote_ssh}:${remote_dir}/${test_file} 2>&1 | grep "Bytes per second:" | tr -d [A-Z][a-z]:, | awk '{ print $1 }')
    else
        echo "cipher: $cipher"
        down_speed=$($scp -v -c $cipher -P $port_num $test_file ${remote_ssh}:${remote_dir}/${test_file} 2>&1 | grep "Bytes per second:" | tr -d [A-Z][a-z]:, | awk '{ print $1 }')
    fi
    if ! which bc &> /dev/null; then
        echo "bc is not installed, cannot provide MB/s or MiB/s conversions"
        echo "down speed: $down_speed B/s"
        echo "pull speed: $pull_speed B/s"
    else
        down_speed_mb=$(echo "($down_speed / 1000) / 1000" | bc)
        #down_speed_mib=$(echo "($down_speed / 1024) / 1024" | bc)
        echo "speed: $down_speed_mb MB/s"
        #echo "speed: $down_speed_mib MiB/s"
    fi

    ssh $remote_ssh "rm ${remote_dir}/${test_file}"
    check_previous "failed to remove remote ${remote_dir}/${test_file}"
    rm ${pwd}/${test_file}
    check_previous "failed to remove ${pwd}/${test_file}"
fi
