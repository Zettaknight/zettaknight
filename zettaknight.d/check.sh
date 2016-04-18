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



#global to disable coloring for printcolors function
color_flag=1 # 0 = nocolor, 1 = color
date_time=$(date '+%Y%m%d_%H%M')

#source helper functions
running_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
printcolors="${running_dir}/printcolors.sh"
source $printcolors || { echo "failed to source $printcolors"; exit 1; }

function check_previous () {
    local exit_status=$?
    local msg="$@"

    if ! [ $exit_status == 0 ]; then
        echo "${exit_status} : $@"
        exit 1
    fi
}

function check_pipes () {
        local pipe_exit_status=$(echo ${PIPESTATUS[*]})
        local msg="$@"
        n=1
        for i in $pipe_exit_status; do
                if ! [ $i == 0 ]; then
                        failed=$(echo "$msg" | cut -d "|" -f${n})
                        echo "$@"
                                if [ $i == 141 ]; then
                                        echo "Failed to pipe output of command: $failed"
                                        exit 1
                                else
                                        echo "$i : $failed"
                                        exit 1
                                fi
                fi
        n=$(( $n + 1 ))
        done
}


function check () {

        local command="$@"
        verbose_flag=1

        date=$(printcolors "yellow" "[$date_time]")
        command_out="$date $command"
        echo "$command_out"

        has_pipes_flag=0
        num_pipes=$(echo $command | grep -o "|" | wc -l)
                if [ $num_pipes -ge 1 ]; then
                        set -o pipefail
                        eval $command
                        check_previous eval $command
                        set +o pipefail
                else
                        eval $command
                        check_previous eval $command
                fi
}
