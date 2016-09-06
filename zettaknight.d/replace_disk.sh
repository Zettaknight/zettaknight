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
version="0.0.4"

#source helper functions
running_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
setopts="${running_dir}/setopts.sh"
source $setopts || { echo "failed to source $setopts"; exit 1; }
zpool="/sbin/zpool"

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
    ret_val=$?
    
    if [ "$ret_val" -ne 0 ]; then
        echo "${ret_val}: $@"
        exit 1
    fi
}

set -e

setopts var "-d|--disk" "disk" "disk to be replaced"
setopts var "-s|--spare" "spare" "disk to replace disk defined in -d"
setopts int "-a|--ashift" "ashift" "ashift value"
setopts var "-p|-zpool" "zpool" "zpool disk in -d is owned by"

echo -e"zpool ${zpool}:\n\treplacing $disk with $spare"

if [ -z "$ashift" ]; then
    $zpool replace -o $zpool $disk $spare
else
    $zpool replace -o ashift=${ashift}  $zpool $disk $spare
fi

