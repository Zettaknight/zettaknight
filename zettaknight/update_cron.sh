#!/bin/bash

version="1.0"
function show_help () {
cat <<EOF

version $version

USAGE:
$0 [lhHmMdD]

DESCRIPTION:
        $(basename $0) takes string passed in a and updates to crontab, appends new strings.
        All time entries are by default a recurring time interval.

OPTIONS:
REQUIRED:
    -l line to be added to crontab
    crontab interval, one of the following is required, one of each pair can be called
        -h hour x
        -H every x hour
        
        -m minute x
        -M every x minute
        
        -d day x
        -D every x day
		
OPTIONAL:
	-r cron string to replace string found in -l

EOF
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


while getopts "l:r:h:H:m:M:d:D::?" OPTION
do
    case $OPTION in
        l)
            line="$OPTARG"
            ;;
		r)
			replace_line="$OPTARG"
			;;
        h)
            cron_hours=$OPTARG
            ;;
        H)
            cron_every_hours=$OPTARG
            ;;
        m)
            cron_mins=$OPTARG
            ;;
        M)
            cron_every_mins=$OPTARG
            ;;
        d)
            cron_days=$OPTARG
            ;;
        D)
            cron_every_days=$OPTARG
            ;;
        :)
            show_help
            ;;
        help)
           show_help
            ;;
    esac
done

if [ -z "$line" ]; then
    echo "cron string is required"
    show_help
    exit 1
fi

if [ -z $cron_hours ] && [ -z $cron_mins ] && [ -z $cron_days ] && [ -z $cron_every_hours ] && [ -z $cron_every_mins ] && [ -z $cron_every_days ]; then
    echo -e "\ninvalid arguments\n"
    show_help
    exit 1
fi

if ! [ -z $cron_every_hours ] && ! [ -z $cron_hours ]; then
    echo "-h and -H cannot be used together"
    show_help
    exit 1
fi
if ! [ -z $cron_every_hours ]; then
    hours="*/${cron_every_hours}"
elif ! [ -z $cron_hours ]; then
    hours=$cron_hours
else
    hours="*"
fi


if ! [ -z $cron_every_mins ] && ! [ -z $cron_mins ]; then
    echo "-m and -M cannot be used together"
    show_help
    exit 1
fi
if ! [ -z $cron_every_mins ]; then
    mins="*/${cron_every_mins}"
elif ! [ -z $cron_mins ]; then
    mins=$cron_mins
else
    mins="*"
fi

if ! [ -z $cron_every_days ] && ! [ -z $cron_days ]; then
    echo "-d and -D cannot be used together"
    show_help
    exit 1
fi
if ! [ -z $cron_every_days ]; then
    days="*/${cron_every_days}"
elif ! [ -z $cron_days ]; then
    days=$cron_days
else
    days="*"
fi


number_of_lines_returned=$(crontab -l | cut -d " " -f 6- | grep -v "^#" | grep "$line" | wc -l)
if [[ $number_of_lines_returned -gt 1 ]]; then
    echo "multiple matches in cron : $number_of_lines_returned, for $line"
    exit 1    
fi
      
cron_time="${mins} ${hours} ${days} * *"

if [ -z "$replace_line" ]; then
	cron_line="${cron_time} ${line}"
else
	cron_line="${cron_time} ${replace_line}"
fi

found_string_flag=0

set -f #turn off globbing to match *'s in crontab
while read -r while_line; do 
    if [[ "$cron_line" == "$while_line" ]]; then
        found_string_flag=1
    fi
done < <(crontab -l)
set +f


if ! [[ $found_string_flag == 1 ]]; then
    #cat <(grep -v  "$line" <(crontab -l)) <(echo "$line") | crontab -
    cat <(crontab -l | grep -v "$line") <(echo "$cron_line") | crontab - &> /dev/null
    check_pipes "cat <(crontab -l | grep -v "$line") <(echo "$cron_line") | crontab -"
    echo "crontab successfully updated, added the following entry"
    echo "$cron_line"
else
    echo "$cron_line already exists in crontab"
fi
