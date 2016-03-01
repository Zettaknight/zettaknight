#!/bin/bash

version="0.0.12"

function show_help () {
cat <<EOF

version $version

USAGE:
$0 [dk]

DESCRIPTION:
        $(basename $0) deletes snapshots that are older than -k days for -d dataset.

REQUIRED:
        -d zfs dataset name
        -k delete snapshots that are older than k days
        
OPTIONAL:
        -r remote server information <user@hostname>

EOF
}

function check_previous () {
		local exit_status=$?
		if ! [ $exit_status == 0 ]; then
			echo "${exit_status} : $@"
			clean_up
			exit 1
		fi
}

function ssh_over () {
    ssh_cmd="$@"
    ssh $remote_ssh "$ssh_cmd"
    check_previous "ssh $remote_ssh $@"
    
}

############ flags ################################
###################################################
remote_flag=0

############ global var ###########################
###################################################
zfs="/sbin/zfs"

#create an ssh key and add it to a remote server
while getopts "d:k:r::?" OPTION
do
        case $OPTION in
                d)
                        dataset=$OPTARG
                        ;;
                k)
                        day_keep=$OPTARG
                        ;;
                r)
                        remote_ssh=$OPTARG
                        remote_flag=1
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

if [ -z $day_keep ] || [ -z $dataset ]; then #both arguments are required, exit if either of them are empty
        echo -e "\n required arguments missing \n"
        show_help
        exit 1
fi

echo "$dataset: destroying snapshots older than $day_keep days"

for i in $($zfs list -H -o name,creation -t snapshot | grep -w $dataset | awk '{print $1"@"$3"@"$4"@"$5"@"$6}'); do
    snapshot=$(echo "$i" | awk 'BEGIN {FS="@"}{print $1"@"$2}')
    snapday=$(echo "$i" | awk 'BEGIN {FS="@"}{print $3" "$4" "$5" "$6}')
    snapsecs=$(date --date="$snapday" +%s)
    today=$(date +%Y%m%d)
    todaysecs=$(date --date="$today" +%s)

    sec_old=$(( $todaysecs - $snapsecs ))
    day_old=$(( $sec_old / 86400 ))

    if [[ $day_old -ge $day_keep ]]; then
        $zfs destroy $snapshot
        logger -p info "$0 destroyed snapshot $snapshot because it was older than $day_keep days."
        echo "destroyed : $snapshot"
#	else
#		echo "$snapshot is $day_old day(s) old, this does not exceed the limit of $day_keep day(s)"
    fi

done