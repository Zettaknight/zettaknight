#!/bin/bash

#source helper functions
running_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
setopts="${running_dir}/setopts.sh"
source $setopts || { echo "failed to source $setopts"; exit 1; }
zpool="/sbin/zpool"

function show_help () {
cat << EOF
version $version

    DESCRIPTION:
        $(basename $0) is used to create a luks container on a disk.

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

setopts var "-d|--disk" "disk" "disk create a luks container on"
setopts var "-k|--keyfile" "keyfile" "keyfile to be added to luks disk."

if [ -z "$keyfile" ] || [ -z "$disk" ]; then

    echo -e "\nrequired arguments missing\n"
    show_help
    exit 1

fi

if ! [ -e "$keyfile" ] || ! [ -e "$disk" ] ; then

    echo "$keyfile or $disk does not exist"
    show_help
    exit 1
        
fi

password="as;lsda;kDFSajgjlk4;kj4a;derp" #default password, will be removed once a key is added to the container
#kirby=([1]="<(o_0<)" [2]="<(o_0)>" [3]="(>o_0)>" [4]="<(o_0)>")

luks_name=$(echo $disk | sed 's/[/]//g')

#cryptsetup luksClose $luks_name || echo "$luks_name is not mounted"

echo -e "\ncreating luks container $luks_name\n\tcryptsetup --cipher aes-xts-plain --key-size 512 --hash sha256 luksFormat $disk <<< <password omitted>"
sudo cryptsetup --cipher aes-xts-plain --key-size 512 --hash sha256 luksFormat $disk <<< $password
check_previous "failed to create LUKS volume on $disk"

echo -e "\nadding keyfile $keyfile to $luks_name\n\tcryptsetup luksAddKey $disk $keyfile <<< <password omitted>"
sudo cryptsetup luksAddKey $disk $keyfile <<< $password
check_previous "failed to add $keyfile to $disk"

echo -e "\nmounting $luks_name\n\tcryptsetup luksOpen $disk $luks_name <<< <password omitted>"
sudo cryptsetup luksOpen $disk $luks_name <<< $password
check_previous "failed to mount LUKS volume $disk as $luks_name"

echo -e "\nconfiguring /etc/crypttab\n\t$luks_name\t$disk\t$keyfile\tluks"
echo -e "$luks_name\t$disk\t$keyfile\tluks" >> /etc/crypttab
check_previous "failed to add information to /etc/crypttab"

#remove original key
echo -e "\nremoving default password\n\tcryptsetup luksKillSlot $disk 0 --key-file $keyfile"
sudo cryptsetup luksKillSlot $disk 0 --key-file $keyfile
check_previous "failed to remove key slot 0"