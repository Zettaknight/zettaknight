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

version="0.0.1"

#source helper functions
running_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
setopts="${running_dir}/setopts.sh"
source $setopts || { echo "failed to source $setopts"; exit 1; }

#authors
#Matthew Carter <mcarte4@clemson.edu>
#Ralph Goodberlet <rgoodbe@clemson.edu>

#######################################
##### function declarations ###########
#######################################

function show_help () {
cat <<EOF

version $version

USAGE:
$0 [dugh]

DESCRIPTION:
        Creates a ZFS dataset for supplied user or group and sets ACL permissions for CIFS sharing.

OPTIONS:
        $setopts_help

EOF
}

function check_previous () {
    local exit_status=$?
    local msg="$@"

    if ! [ $exit_status == 0 ]; then
        echo "${exit_status} : $@"
        clean_up
        exit 1
    fi
}

function clean_up () {
  if [ -n $dset ]; then
    $zfs destroy $dset
    $logger -p info "$0 destroyed dataset $dset at $date_time because the script encountered an error and could not continue."
  fi
}

function find_call () {

    local call=$1
    local var_declare=$2 #what variable name you would like to set the call in $1 to be
    local need_sudo=$3 #if the user is not root, will it need sudo?

    local path=("/usr/local/sbin" "/usr/local/bin" "/sbin" "/bin" "/usr/sbin" "/usr/bin" "/root/bin")
    local found_flag=0


    for loc in ${path[@]}; do
        local full_path="${loc}/${call}"
        if [ $found_flag == 0 ]; then
            if [ -x $full_path ]; then
                #echo -e "${call}=${full_path}"
                found_flag=1

                if [ -z "$var_declare" ]; then
                    local final_call="$call"
                else
                    local final_call="$var_declare"
                fi

                if ! [ -z "$need_sudo" ]; then #if user is not root append sudo to each command
                    if [ $(id -u) != 0 ]; then
                        local full_path="sudo "${full_path}
                    fi
                fi

                eval $final_call"=\"\$full_path\""

            fi
        fi
    done


    if [ $found_flag == 0 ]; then
        echo -e "call $call not found, cannot continue"
        exit 1
    fi
}

#######################################
######### set/declare flags ###########
#######################################
display_help_flag=0

#######################################
##### set/declare variables ###########
#######################################

setopts var "-u|--user" "user" "User to create a new share for.  If group  is not specified, user is required."
setopts var "-g|--group" "group" "Group to create a new share for.  If user is not specified, group is required."
setopts var "-d|--dataset" "dataset_root" "Parent dataset where new user/group dataset should be nested under.  ie. -d 'tank' -u 'bob' will create dataset tank/bob.  This argument is always required."
setopts var "-p|--permissions" "perms" "Posix permissions to apply to newly created user or group directories.  By default, user directories will be created with user-only permissions, and group directories will be created with user/group permissions.  Permissions must be supplied in posix format, ie 'u+rwxs,g-rx,o-rwx'"

setopts flag "-h|--help" "display_help_flag" "Shows this help dialogue."
date_time=$(date '+%Y%m%d_%H%M')

if [ $display_help_flag == 1 ]; then
  show_help
  exit 1
fi

find_call "zfs"
find_call "chmod"
find_call "chown"
find_call "chgrp"
find_call "setfacl"
find_call "logger"

#######################################
############ script start #############
#######################################

if [ -z $dataset_root ]; then
  echo -e "\nRequired argument(s) missing.\n"
  show_help
  exit 1
fi

if [ -z $user ] && [ -z $group ]; then
  echo -e "\nRequired argument(s) missing.\n"
  show_help
  exit 1
fi

if ! [ -z $user ] && ! [ -z $group ]; then
  echo -e "\nSpecifying both user and group is not supported."
  show_help
  exit 1
fi

if ! [ -z $user ]; then
  dset="${dataset_root}/${user}"
else
  dset="${dataset_root}/${group}"
fi
dir=$(echo "/${dset}")
  
#######################################

$zfs create $dset
check_previous "$zfs create $dset"

$logger -p info "$0 created dataset $dset at $date_time"

if ! [ -z $user ]; then
  if [ -z $perms ]; then
    perms="u+rwxs,g-rwx,o-rwx"
  fi
  
  $chmod $perms $dir
  check_previous "$chmod $perms $dir"
  
  $setfacl -m u:${user}:rwx $dir
  check_previous "$setfacl -m u:${user}:rwx $dir"
  
  $chown $user $dir
  check_previous "$chown $user $dir"
  
  $logger -p info "$0 set posix permissions $perms on $dset and added rwx acl permissions for user: $user at $date_time"
  
  echo "Share for user: $user created successfully."
  
elif ! [ -z $group ]; then
  if [ -z $perms ]; then
    perms="u+rwx,g+rwxs,o-rwx"
  fi
  
  $chmod $perms $dir
  check_previous "$chmod $perms $dir"
  
  $setfacl -m g:${group}:rwx $dir
  check_previous "$setfacl -m g:${group}:rwx $dir"
  
  $chgrp $group $dir
  check_previous "$chgrp $group $dir"
  
  $logger -p info "$0 set posix permissions $perms on $dset and added rwx acl permissions for group: $group at $date_time"

  echo "Share for group: $group created successfully."
  
fi

exit 0

