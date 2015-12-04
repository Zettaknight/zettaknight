#!/bin/bash

version="2.1"
#set -x

#authors:
#Matthew Carter <mcarte4@clemson.edu>
#Ralph Goodberlet <rgoodbe@clemson.edu>

#restore luks header
        #cryptsetup luksHeaderRestore <device> --header-backup-file <file>
#how to erase luks header
        #head -c 3145728 /dev/zero > /dev/sdb2; sync
#add detail information into first line of crypttab




##########################################################################
########################### flags ########################################
##########################################################################
luks_flag=0
initialize_flag=0
luks_header_backup_flag=0
create_dataset_flag=0
slog_flag=0


##########################################################################
################### zfs variables ########################################
##########################################################################
ashift_val=9 #default 0 is auto-detect, advanced 4k sector drives will be 12, CANNOT be empty
zpool_autoreplace="on" #must be exactly on or off, no exceptions
compression="off" #"on", "off", "lzjb", "lz4", "gzip", "gzip[1-9]", and "zle"
record_size=1M
aclinherit="restricted"
acltype="off"

##########################################################################
################ global variables ########################################
##########################################################################
date_time=$(date +'%Y%m%d')
logfile=$0.log_${date_time}
working_dir=$(pwd) #make sure starting directory is preserved
hostname=$(hostname | cut -d . -f 1)
doc_source="https://twiki.clemson.edu/bin/view/CSOKBase/KBaseU1428510436#SVN_doesn_t_work_the_script_is_b"
logfile="$0.log"
disk_path="/dev/disk/by-id/dm-uuid-mpath-*" #if file is not given, default location to look for mpath devices

function show_help () {
cat <<EOF

version $version

USAGE:
$0 [fdzplbs]

DESCRIPTION:
        $(basename $0) is used to create a zfs zpool. A file is read in for disks to
        be used in the zpool creation, separated by \n.  If the file does not exist,
        $0 will attempt to create the disk list from all devices found in
        $disk_path.

        In a standard 4+1, there are essentially 4 data disks, plus a single parity
        disk. This concept is used to create the underlying zpool. If a 4+1
        architecture is desired, simply declare -d 4 to denote the 4 data disks,
        and set the corresponding zpool level you want.  In this case -z 1 for the
        raidz1 option.  The function will then take all disks passed in from -f and
        increment as many volumes as necessary to fulfill the request.  I.E.,
        40 disks passed in with -f would create 8 volumes of 4+1 in the zpool.

        If there are any disks left over but are not enough to
        create another volume, they are automatically allocated as spare.

        The luks headers can be backed up on creation and will dump in $0.file.

        Luks encryption is available with -l. When envoked, a luks container will be
        created for each device read in from -f.  A plain text default password will
        be used for initial creation, and a RSA 4096 bit key will be added to the
        volume to be automounted.  If the key does not exist, $keyfile will be
        created. Once the key is added to the volume, the plain text password will
        be removed leaving only the key for mounting the volume.  The neccessary
        information is the added in /etc/crypttab so it may mount at boot before
        zfs loads.

        Backing up the luks header is essential since if the luks metatdata portion
        of the disk is damaged or corrupted, the data on it is unrecoverable.

        A SLOG is an alternate location for the ZIL. Best practices suggest that
        it resides on a 1+1 mirror. If more than 2 disk are given, it will continue
        to create and add 1+1 mirrors until there are not enough disks to satisfy a
        complete 1+1. It will however allow a single disk to be used.

OPTIONS:
REQUIRED:
        -f list of disks from a file separated by \n
        -d number of data disks per volume. I.E. a 3+1 would have 3 data disks
        -z zpool type, valid options are listed below [0-4]
                0. stripe
                1. raidz1
                2. raidz2
                3. raidz3
                4. mirror
OPTIONAL:
        -p zpool name (if zpool name is not given, a default zfs_data/<hostname> will be created)
        -l add a LUKS container for each disk read in from -f
        -k keyfile to be used for the luks container, if this is empty $keyfile will be created.
        -b backup luks headers on creation
        -s adds a SLOG to the created zpool, list of disks from a file separated by \n. (full path required)

EOF

exit 1 #exit after being helpful
}

function check_previous () {
                if [ $? -ne 0 ]; then
                                echo "error code:$? message:$@"
                                if [ -e $0.new_luks_${date_time} ]; then
                                        rm -f $0.new_luks_${date_time}
                                fi

                                echo -e "\nError documentation available at: \n$doc_source"
                                exit 1
                fi
}

function validate_input () {
        local var=$1
        local var_type=$2
        local var_req=$3 #defines if variable is required

        if [[ -z $var_req ]]; then #if var_req is empty, assume variable is not required
                var_req=0
        fi

        if [[ -z "$var" && $var_req == "required" ]]; then
                echo -e "required argument is missing : $var\n"
                show_help
        fi

        if [[ -n "$var" ]]; then
                if [ $var_type == "int" ]; then
                        if ! [[ $var =~ ^[-+]?[0-9]+$ ]]; then #test if input is an integer
                                echo "$var is not an integer"
                                show_help
                        fi
                fi
                if [ $var_type == "file" ]; then
                        if ! [ -s $var ]; then
                                echo "$var is not a valid file."
                                show_help
                        fi
                fi
        fi
}

function create_array_from_file () {
        local file=$1
        local i=0

        unset array #if array existed before, remove it

        while read line; do

                if [[ -z $line ]]; then
                        echo "$line does not exist, cannot continue"
                        exit 1
                fi
                if ! echo $line | grep '^#' &> /dev/null; then
                        array[$i]="$line"
                        check_previous "array[$i]=$line"
                        i=$(($i + 1))
                fi
        done < $file
}

function create_disk_list () {

        local disk_path=$1
        local disk_count=$(find $disk_path | wc -l)
        local i=0

        if [ $disk_count == 0 ]; then
                echo "No multipath devices found, cannot continue"
                exit 1
        else
                echo "$disk_count disks found"
                for dev in $(find $disk_path); do
                        array[$i]="$dev"
                        check_previous "array[$i]=$dev"
                        i=$(($i + 1))
                done
        fi
}

function create_array_from_string () {
    local string=$1
    
    local i=0

    unset array #if array existed before, remove it
    
    echo "should be creating an array from a string input"
    echo "disk_list : $string"

    for disk in $string; do

        if [[ -z $disk ]] || [[ ! -e $disk ]]; then
                echo "$disk is either empty or does not exist, cannot continue"
                exit 1
        else
            array[$i]="$disk"
            check_previous "array[$i]=$disk"
            i=$(($i + 1))
        fi
        
    done
    
}


function create_luks () {
        #required packages ubuntu
        #cryptsetup

        local password="as;lsda;kDFSajgjlk4;kj4a;derp" #default password, will be removed once a key is added to the container

        if [ -z "$keyfile" ]; then
            keyfile="/root/.ssh/zfs.luks"
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
                check_previous "failed to create $keyfile"
                logger -p info "$0 created keyfile $keyfile"
        fi


        n=0
        #kirby=([1]="<(o_0<)" [2]="<(o_0)>" [3]="(>o_0)>" [4]="<(o_0)>")

        for d in ${array[@]}; do

                i=$(echo $d | awk 'BEGIN {FS="/"} { print $NF }')

                if ! [ -e $d ]; then #if this doesn't exist, then check this prefix to see if exists
                        echo "$d is not a valid device"
                        exit 1
                fi

                #luks_vol="${i}${n}"
                luks_name=$(echo $d | sed 's/[/]//g')

                #cryptsetup luksClose $luks_name || echo "$luks_name is not mounted"

                sudo cryptsetup --cipher aes-xts-plain --key-size 512 --hash sha256 luksFormat $d <<< $password
                check_previous "failed to create LUKS volume on $d"

                sudo cryptsetup luksAddKey $d $keyfile <<< $password
                check_previous "failed to add $keyfile to $d"

                if [ $luks_header_backup_flag == 1 ]; then
                        #create intial backup of luks headers after creation and key file generation
                        sudo cryptsetup luksHeaderBackup $d --header-backup-file "$0.${luks_name}_${date_time}_luks_header_backup"
                        check_previous "failed to backup luks header for $d"
                fi

                sudo cryptsetup luksOpen $d $luks_name <<< $password
                check_previous "failed to mount LUKS volume $d as $luks_name"

                echo -e "$luks_name\t$d\t$keyfile\tluks" >> /etc/crypttab
                check_previous "failed to add information to /etc/crypttab"

                #remove original key
                sudo cryptsetup luksKillSlot $d 0 --key-file $keyfile
                check_previous "failed to remove key slot 0"

                #create new file variable
                echo $luks_name >> $0.new_luks_${date_time}
                check_previous "failed to create/append $0.new_luks_${date_time}"

                n=$(($n + 1))
                k=$n
                while [ $k -gt 4 ];
                        do
                        k=$(($k - 4))
                done
#                echo -ne "${kirby[$k]} completed $n luks containers: $d\r"

        done

        create_array_from_file $0.new_luks_${date_time}
        #ls /dev/mapper/devdisk* | while read line; do cryptsetup luksClose $line; echo -e "\n$line, exit code:$?"; done
}

################################################################################
########################### script start #######################################
################################################################################

while getopts "a:r:d:f:p:k:z:lbis:?" OPTION
do
         case $OPTION in
                 d)
                         data_disks=$OPTARG
                         ;;
                 a)
                         ashift_val=$OPTARG
                         ;;
                 r)
                         record_size=$OPTARG
                         ;;
                 f)
                         file=$OPTARG
                         ;;
                 p)
                         zpool_name=$OPTARG
                         ;;
                 z)
                         zpool_type=$OPTARG
                         ;;
                 l)
                         luks_flag=1
                         ;;
                 b)
                         luks_header_backup_flag=1
                         ;;
                 s)
                         slog_file=$OPTARG
                         slog_flag=1
                         ;;
                 k)
                        keyfile=$OPTARG
                        ;;
                 i)
                        aclinherit="passthrough"
                        acltype="posixacl"
                        ;;
                 :)
                         show_help
                         ;;
                 help)
                         show_help
                         ;;
         esac
done

############## validate inputs ##############
validate_input "$data_disks" int required
validate_input "$zpool_type" string required
validate_input "$zpool_name" string
validate_input "$slog_file" file
validate_input "$ashift_val" int
#############################################

if [ -z "$zpool_name" ]; then  # If no zpool name given, use standard naming
        zpool_name="zfs_data"
        create_dataset_flag=1
fi

#test to make sure -b is not being used without -l
if [[ $luks_header_backup_flag == 1 ]] && [[ $luks_flag == 0 ]]; then
        echo -e "\ncannot use -b without -l\n"
        show_help
fi

if [ $zpool_type == 0 ]; then
                zpool_type=""
                parity=0
elif [ $zpool_type == 1 ]; then
                zpool_type="raidz1"
                parity=1
elif [ $zpool_type == 2 ]; then
                zpool_type="raidz2"
                parity=2
elif [ $zpool_type == 3 ]; then
                zpool_type="raidz3"
                parity=3
elif [ $zpool_type == 4 ]; then
                zpool_type="mirror"
                parity=$data_disks
else
                echo "no valid option selected"
                exit 1
fi


#if no file given, attempt to create a disk list from multipath
if [[ -f "$file" ]]; then
    create_array_from_file "$file"
elif [ ! -z "$file" ]; then
    create_array_from_string "$file"        
else
    create_disk_list "$disk_path"
fi

total_disks=$(echo ${#array[*]}) #number of volumes
disk_in_vol=$(($data_disks + $parity))
remainder=$(($total_disks % $disk_in_vol))
disk_in_pool=$(($total_disks - $remainder))
spares=$(( $total_disks - $disk_in_pool ))
how_many_loops=$(($disk_in_pool / $disk_in_vol))

if [ $how_many_loops == 0 ]; then
        echo "not enough disks, cannot create ${data_disks}+${parity} from $total_disks disks"
        exit 1
fi

if [ $luks_flag == 1 ]; then #must come after array declaration
        create_luks
fi

loop_count=0 #current times through the loop
array_count=0 #how many indexes of the array have been used

while [[ $loop_count -lt $how_many_loops ]]; do
        volume_disk_count=1 #1 instead of 0 to stop extra loop and make the disk count usable without subtraction
        while [[ $volume_disk_count -le $disk_in_vol ]]; do
                var="${array[$array_count]} $var"
                volume_disk_count=$(($volume_disk_count + 1))
                array_count=$(($array_count + 1))
        done
                var="$zpool_type $var"
                loop_count=$(($loop_count + 1))
done

s=0 #calclate spares
while [[ $array_count -lt $total_disks ]]; do
        var2="${array[$array_count]} $var2"
        array_count=$(($array_count + 1))
done

if ! [ $remainder == 0 ]; then
        var="$var""spare $var2"
fi

zpool create -f "$zpool_name" -o ashift=${ashift_val} -o autoreplace=${zpool_autoreplace} -O recordsize=${record_size} -O xattr=sa -O aclinherit=$aclinherit -O acltype=$acltype -O compression=${compression} $var
check_previous "FAILED : zpool create $zpool_name -o ashift=${ashift_val} -o autoreplace=${zpool_autoreplace} -O xattr=sa -O compression=${compression} $var"
logger -p info "$zpool_name zpool created by $0"


if [ $slog_flag == 1 ]; then
        #do something with a log here
        create_array_from_file $slog_file

        slog_disks=$(echo ${#array[*]})
        slog_vols=$(( $slog_disks / 2 ))
        array_count=0

        if [ $slog_disks == 1 ]; then
           zpool add $zpool_name log ${array[0]}
           check_previous "zpool add $zpool_name log ${array[0]}"
           logger -p info "slog added to $zpool"
        fi
        while [ $slog_vols -gt 0 ]; do
                slog="${array[$array_count]} $slog"
                array_count=$(($array_count + 1 ))
                slog="${array[$array_count]} $slog"
                array_count=$(($array_count + 1 ))
                zpool add $zpool_name log mirror $slog
                check_previous "zpool add $zpool_name log mirror $slog by $0"
                logger -p info "mirrored slog added to $zpool by $0"
                slog=""
                slog_vols=$(($slog_vols - 1 ))
                if [[ $slog_vols -lt 1 ]] && [[ $slog_vols -gt 0 ]]; then
                        echo "An odd but greater than 1 number of disks was provided in $slog_file."
                        echo "${array[$array_count]} referenced in $slog_file was ignored."
                fi
        done

fi

#if local pool name if default
if [ $create_dataset_flag == 1 ]; then # if using standard naming, deploy hostname based 'root' dataset
        zfs create ${zpool_name}/${hostname}
        check_previous "zfs create ${zpool_name}/${hostname}"
        logger -p info "zfs dataset $zpool_name/$hostname create by $0"
fi

echo "$(zpool status)"
echo -e "\ndancing Kirby approves!"
echo -e "<(o_0<) <(o_o)> (>0_o)>\n"

if [ -e $0.new_luks_${date_time} ]; then
        rm -f $0.new_luks_${date_time}
        check_previous "failed to remove $0.new_luks_${date_time}"
fi