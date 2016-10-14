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

version="1.3"

### to do list ####
#test if remote located headers are the same as the ones being backup up / md5 (-v verify)

#authors
#Matthew Carter <mcarte4@clemson.edu>
#Ralph Goodberlet <rgoobe@clemson.edu>

######################################################
################ global variables ####################
######################################################
date_time=$(date '+%Y%m%d_%H%M')
#pwd="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
delete_flag=0
remote_backup_flag=0
local_only_flag=0
#local_backup_dir="${pwd}/${date_time}_$(hostname)_luks_header_backups"
######################################################
############ end global variables ####################
######################################################

######################################################
############ function declarations ###################
######################################################

function show_help () {
cat <<EOF

version $version

USAGE:
$0 [lrds]

DESCRIPTION:
        $(basename $0) will backup luks headers from devices defined in /etc/crypttab.

OPTIONS:
        -l local only option, will create backups locally to this directory, full path required, cannot be used with other options
        -r remote directory location for luks header backups
                -d delete local files after commiting to remote location
                -s remote ssh options [user@host], will need permissions to write to remote directory declared in -r
EOF
}

function clean_up () {
    if [ -e $local_backup_dir ]; then
        echo "cleaning up : rm -rf $local_backup_dir"
        rm -rf $local_backup_dir
    fi
}

function check_previous () {
        local exit_status=$?
        if ! [ $exit_status == 0 ]; then
            echo -e "\n${exit_status} : $@"
            #clean_up
            exit 1
        fi
}
######################################################
######## end function declarations ###################
######################################################

while getopts "l:r:s:d?" OPTION
do
     case $OPTION in
        l)
            local_backup_dir=$OPTARG
            local_only_flag=1
            case $local_backup_dir in
                */) ;;
                *) local_backup_dir="${local_backup_dir}/";;
            esac
            ;;
        r)
            remote_backup_dir=$OPTARG
            remote_backup_flag=1
            case $remote_backup_dir in
                */) ;;
                *) remote_backup_dir="${remote_backup_dir}/";;
            esac
            ;;
        s)
            remote_ssh=$OPTARG
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

######################################################
############ script start ############################
######################################################

#has to be declared after getopts statement, needs var $remote_ssh
remote_host=$(echo ${remote_ssh} | cut -d "@" -f2)
cryptsetup="/sbin/cryptsetup"

#if no options are selected, show help
if [ $local_only_flag == 0 ] && [ $remote_backup_flag == 0 ]; then
    show_help
    exit 1
fi

#if local flag is called, make sure other flags are not being used
if [ $local_only_flag == 1 ]; then
    if [ ! -z $remote_backup_dir ] || [ ! -z $remote_ssh ] || [ $delete_flag == 1 ]; then
        echo "-l option cannot be used with other options"
        show_help
        exit 1
    fi
fi

#check if -s and -d options are being used without -r
if [ $remote_backup_flag == 0 ]; then
    if [ ! -z $remote_ssh ] || [ $delete_flag == 1 ]; then
        echo "-s and -d options cannot be used without -r"
        show_help
        exit 1
    fi
fi

#make sure -s and -r are used together
if [ $remote_backup_flag == 1 ] && [ -z $remote_ssh ]; then
    echo "-s must be used with -r"
    show_help
    exit 1
fi

#make sure remote backup directory exists
if [ $remote_backup_flag == 1 ]; then
    if ! ssh -t $remote_ssh "[ -d $remote_backup_dir ]"; then
        echo "failed to connect to remote backup directory $remote_backup_dir using $remote_ssh"
        clean_up
        exit 1
    fi
fi

if ! [[ -e "$local_backup_dir" ]]; then
    echo "creating $local_backup_dir"
    mkdir -p $local_backup_dir
    check_previous "mkdir -p $local_backup_dir"
    echo -e "created $local_backup_dir\n"
fi

#read in /etc/crypttab for active luks devices on host
while read line; do
    disk=$(echo $line | awk '{print $2}')
    luks_name=$(echo $disk | sed 's/[/]//g')
    #luks_backup_file="${local_backup_dir}${date_time}_${luks_name}_luks_header_backup"
    luks_backup_file="${local_backup_dir}${luks_name}"
        
    if ! [[ -z "$disk" ]]; then
        sudo $cryptsetup luksHeaderBackup $disk --header-backup-file "$luks_backup_file"
        if [ $? == 0 ]; then
            echo "created $luks_backup_file"
        fi
    fi

done < "/etc/crypttab"

if [ $remote_backup_flag == 1 ]; then
    remote_backup_file="${remote_backup_dir}${date_time}_${luks_name}_luks_header_backup" #no slash after remote_backup_dir, easier to add a trailing slash to user input that remove it, only one that's different
    scp -r $local_backup_dir ${remote_ssh}:${remote_backup_dir}${date_time}_$(hostname)_luks_header_backups
    check_previous "scp -r $local_backup_dir ${remote_ssh}:${remote_backup_dir}${local_backup_dir}"
    echo -e "\ncopied $local_backup_dir to $remote_host"
fi

if [ $delete_flag == 1 ]; then
    clean_up
fi
