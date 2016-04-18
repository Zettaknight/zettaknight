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
#source helper functions
running_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
setopts="${running_dir}/setopts.sh"
source $setopts || { echo "failed to source $setopts"; exit 1; }
date_time=$(date +'%Y%m%d')

poll_int=1
poll_count=10
tail_num=$((${poll_count} - 1))
outfile="${running_dir}/${date_time}_$(basename $0)"

setopts var "-f|--outfile" "outfile" "file to write results to (default:${outfile})"

zpool="/sbin/zpool"

for pool in $($zpool list -H -o name); do
    if ! [ -z "$pool" ]; then
        date_log=$(date +'%Y%m%d%H%M%S')
        human_date_log=$(date +'%Y-%m-%d_%H.%M.%S')
        echo "$human_date_log" | tee -a $outfile
        $zpool iostat $pool $poll_int $poll_count | tail -${tail_num} | awk 'BEGIN { OFS=","} {rops=rops+$4} {wops=wops+$5} {rband=rband+$6} {wband=wband+$7} END {print $1, $2, $3, rops/NR, wops/NR, rband/NR, wband/NR}'  | tee -a $outfile
    fi
done
