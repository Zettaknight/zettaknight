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

version="1.2"

#delete all zfs related stuff

#authors: 
#Matthew Carter <mcarte4@clemson.edu>
#Ralph Goodberlet <rgoodbe@clemson.edu>
#Matthew Carter
#Ralph Goodberlet

function show_help () {
cat <<EOF

version $version

USAGE:
$0 [pf]

DESCRIPTION:
        $(basename $0) is used to delete zfs zpools. If the zpool was created on a luks container,
        that container will be closed and the corresponding entry from /etc/crypttab will
        be removed. If an NFS export was shared via /etc/exports, the corresponding entry will be commented
        out.

OPTIONS:
        -p zpool name to be destroyed ($zpool_name)  --required
        -f (force) option is provided for automation purposes, without guarantees. Use at your own risk.
EOF
}

function check_previous () {
    exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo "exit_status:${exit_code} message: $@"
        exit 1
    fi
}

force_flag=0

if [ $(id -u) -ne 0 ]; then
    zfs="/sbin/zfs"
else
    zfs="sudo /sbin/zfs"
fi

while getopts "p:f?" OPTION
do
     case $OPTION in
         p)
             zpool_name=$OPTARG
             ;;

         f)
            force_flag=1
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

if [ -z "$zpool_name" ]; then
    show_help
    exit 1
fi

if [ $force_flag = 0 ]; then
    echo "This script will destroy all ZFS components for $zpool_name"
    read -p "Type DELETE to continue: " answer
    if ! [[ $answer == "DELETE" ]]; then
        echo "$answer =/= DELETE exiting"
        exit 1
    fi
fi

zpool list "$zpool_name"
check_previous "ERROR:  $zpool_name is not a valid zpool."

#if zpool does contain luks devices
marker=0
for pool in $(zpool status "$zpool_name" | awk '{print $1}'); do

    while read line; do
        #all variables, declared in while loop
        disk=$(echo $line | grep "$pool" | awk '{print $1}')
        is_luks=$(echo $line | grep "$pool" | awk '{print $4}')

        shopt -s nocasematch #used in case $is_luks statement is case insensitive
        if [[ "$is_luks" == "luks" ]]; then
            #comment out nfs shares / exportfs -arv if marker=0
            if [ $marker == 0 ]; then
                $zfs list "$zpool_name" | grep "$zpool_name" | awk '{ print $5 }' | while read line; do
                    sed -i "s@^${line}@#${line}@" /etc/exports
                    check_previous "sed -i "s@^${line}@#${line}@" /etc/exports"
                    if [ $force_flag = 0 ]; then
                        echo "Removed $zpool_name from /etc/exports"
                    fi
                done
                exportfs -ar
                check_previous "ERROR exports -ar"
            fi

            #destroy pool if marker=0
            if [ $marker == 0 ]; then
                zpool destroy -f "$zpool_name"
                check_previous "ERROR zpool destroy -r $zpool_name"
                logger -p info "$0 deleted zpool $zpool_name"
                marker=1
            fi

            if [ -e /dev/mapper/$disk ]; then
                #if luks / close luks
                cryptsetup luksClose /dev/mapper/$disk
                check_previous "ERROR cryptsetup luksClose $disk"
                if [ $force_flag = 0 ]; then
                    echo "Closed $disk"
                fi
            else
                echo "$disk is defined in crypptab but not in /dev/mapper"
            fi
                #remove /etc/crypttab entries
            ln=$(grep -m 1 -n "$line" /etc/crypttab | cut -d ":" -f1)

            if ! [[ $ln =~ ^[-+]?[0-9]+$ ]]; then #check if ln returns multiple lines
                echo "$ln is not an integer"
                exit 1
            fi

            sed -i "${ln} d" /etc/crypttab
            check_previous "ERROR sed -i "${ln} d" /etc/crypttab"
            logger -p info "$0 removed $line from /etc/crypttab"

            if [ $force_flag = 0 ]; then
                echo "Crypttab entry for $disk removed"
            fi
        fi
    done < /etc/crypttab

        #if zpool does not contain luks devices
        if [ $marker == 0 ]; then
            $zfs list "$zpool_name" | grep "$zpool_name" | awk '{ print $5 }' | while read line; do
                sed -i "s@^${line}@#${line}@" /etc/exports
                check_previous "sed -i "s@^${line}@#${line}@" /etc/exports"
                if [ $force_flag = 0 ]; then
                    echo "Removed $zpool_name from /etc/exports"
                fi
            done
            
            if $(which exportfs); then
                exportfs -ar
                check_previous "ERROR exports -ar"
            fi
            
            zpool destroy -f "$zpool_name"
            check_previous "ERROR zpool destroy -r $zpool_name"
            logger -p info "$0 deleted zpool $zpool_name"
            marker=1
        fi
done

echo "$zpool_name has been deleted"
