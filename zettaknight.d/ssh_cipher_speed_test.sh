#!/bin/bash

version=0.1

####### global variables #############
dd_bs=1000000
dd_count=1000
remote_ssh="localhost" #default value
######################################

####### flags ########################
run_flag=0
######################################

function show_help () {
cat <<EOF

version $version

USAGE:
$0 [ar]

DESCRIPTION:
	$(basename $0) tests ssh ciphers speeds. 

OPTIONS:
REQUIRED:
	-a run all tests
OPTIONAL:
	-r remote ssh credentials to test remote server (format: <user@host>)
	
EOF

exit 1 #exit after being helpful
}

#if not remote_host, assume localhost
while getopts "ar::?" OPTION
do
	case $OPTION in
		a)
			run_flag=1
			;;
		r)
			remote_ssh=$OPTARG
			;;
		:)
			show_help
			;;
		help)
			show_help
			;;
	esac
done

if [ $run_flag == 0 ]; then
	show_help
fi

if [ -s /etc/os-release ]; then
	cipherlist=$(ssh -Q cipher)
else
	cipherlist=$(cat /etc/ssh/sshd_config | grep Ciphers | awk '{print $NF;}' | awk 'BEGIN {RS=","; FS=","; OFS=" ";} {print;}')
fi

for cipher in $cipherlist; do
	echo -e "\n$cipher"
	dd if=/dev/zero bs=${dd_bs} count=${dd_count} | ssh -c $cipher $remote_ssh "cat > /dev/null"
done