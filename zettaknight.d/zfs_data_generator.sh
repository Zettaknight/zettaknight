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
setopts var "-p|--zpool" "zpool" "zpool to show iostat data for, if empty, all pools will be shown"

zpool="/sbin/zpool"

if [ -z $zpool ]; then
    mystring="$($zpool list -H -o name)"
else
    mystring="$zpool"
fi

for pool in $mystring; do
    if ! [ -z "$pool" ]; then
        date_log=$(date +'%Y%m%d%H%M%S')
        human_date_log=$(date +'%Y-%m-%d_%H.%M.%S')
        echo "$human_date_log" | tee -a $outfile
        $zpool iostat $pool $poll_int $poll_count | tail -${tail_num} | awk 'BEGIN{k=1000;m=1000*k;g=1000*m;OFS=","} {x=substr($5,1,length($5)-1)*1} $5~/[Kk]$/{x*=k} $5~/[mM]$/{x*=m} $5~/[Gg]$/{x*=g} $5~/[01234567890]$/{x=$5} {wops=wops+x} {x=substr($4,1,length($4)-1)*1} $4~/[Kk]$/{x*=k} $4~/[mM]$/{x*=m} $4~/[Gg]$/{x*=g} $4~/[01234567890]$/{x=$4} {rops=rops+x} {x=substr($6,1,length($6)-1)*1} $6~/[Kk]$/{x/=k} $6~/[mM]$/{x=$6} $6~/[Gg]$/{x*=k} $6~/[01234567890]$/{x/=m} {rband=rband+x} {x=substr($7,1,length($7)-1)*1} $7~/[Kk]$/{x/=k} $7~/[mM]$/{x=$7} $7~/[Gg]$/{x*=k} $7~/[01234567890]$/{x/=m} {wband=wband+x} END {print $1, $2, $3, rops/NR, wops/NR, rband/NR, wband/NR}'  | tee -a $outfile
    fi
done
