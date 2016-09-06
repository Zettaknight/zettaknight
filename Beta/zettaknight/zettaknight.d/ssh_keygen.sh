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

#version information
version="1.1"

#global variables
date_time=$(date +'%Y%m%d')
rsa_key_size=4096
ssh_copy_id=$(which ssh-copy-id)


#flags
remote_ssh_flag=0

function check_previous () {
                if [ $? -ne 0 ]; then
                                echo "error code:$? message:$@"
                                exit 1
                fi
}

function show_help () {
cat <<EOF

version $version

USAGE:
$0 [kr]

DESCRIPTION:
        $(basename $0) creates a $rsa_key_size bit RSA key, and copies it to a remote server.
        
REQUIRED:
        -k name of the keyfile to be created, full path is required. (i.e. $(pwd)/<name>)
OPTIONAL:
        -r remote ssh information for remote copy. Required format is <user@hostname>
        
EOF
}

#create an ssh key and add it to a remote server
while getopts "k:r::?" OPTION
do
        case $OPTION in
                k)
                        keyfile=$OPTARG
                        ;;
                r)
                        remote_ssh=$OPTARG
                        remote_ssh_flag=1
                        ;;
                :)
                        show_help
                        ;;
                help)
                        show_help
                        ;;
        esac
done

#validate inputs
if [ -z $keyfile ]; then
        show_help
    exit 1
fi


if ! [ -e "$keyfile" ]; then #create keyfile if it does not exist
    keyfile_directory=$(dirname $keyfile)
    echo "$keyfile needs to exist for crypttab to open and mount container on boot"
    if ! [ -e "$keyfile_directory" ]; then
        echo "$keyfile_directory does not exist, creating"
        mkdir -p "$keyfile_directory"
        check_previous mkdir -p "$keyfile_directory"
    fi
    echo "creating $keyfile"
    ssh-keygen -t rsa -N "" -C "$date_time automated key creation, luks containers" -f $keyfile -b 4096
    check_previous "FAILED: create keyfile $keyfile"
    logger -p info "$0 created keyfile $keyfile"
else
    echo "$keyfile exists"
fi


#add new keyfile to remote host
if [ $remote_ssh_flag == 1 ]; then
                echo "adding $keyfile to $remote_ssh"
    if which $ssh_copy_id &> /dev/null; then
            $ssh_copy_id -i $keyfile $remote_ssh
            check_previous "ssh-copy-id -i $keyfile $remote_ssh"
    else
        echo "woah, $ssh_copy_id is not available, exiting"
        exit 1    
            
        #ssh $remote_ssh "cat >> \~/.ssh/authorized_keys" <${keyfile}.pub
        
    fi
fi
