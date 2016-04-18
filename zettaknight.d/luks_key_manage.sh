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

version="1.2"

#will read /etc/crypttab a replace keys as necessary
#if keyfile provided, don't create one
#update crypttab for all entries

#authors
#Matthew Carter <mcarte4@clemson.edu>
#Ralph Goodberlet <rgoodbe@clemson.edu>

date_time=$(date +'%Y%m%d')
delete_flag=0

function show_help () {
cat <<EOF

version $version

USAGE:
$0 [kd]

DESCRIPTION:
        $(basename $0) is used to manage keys for luks disk encryption.  This function is designed
        to add the passed in keyfile to add luks partitions defined in /etc/crypttab.
OPTIONS:
        -k keyfile to be added to luks partitions, will be created if it doesn't exist, needs full path i.e. /root/.ssh/<filename>
        -d delete all other keyfile except for the keyfile specified in -k
        
EOF
}

function check_previous () {
        exit_code=$?
        if [ $exit_code -ne 0 ]; then
                echo "exit_status:${exit_code} message:$@"
                if [ -e "$trash_file" ]; then #remove if trash file exists
                        rm -f $trash_file
                fi
                exit 1
        fi
}

while getopts "k:d?" OPTION
do
        case $OPTION in
        k)
                new_keyfile=$OPTARG
                ;;
        d)
                delete_flag=1
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

if [ ! -s "/etc/crypttab" ]; then
    echo "etc/crypttab has no entries, nothing to do"
    exit 0
fi

if [ -z $new_keyfile ]; then
        show_help
        exit 1
fi
    

if ! [ -e "$new_keyfile" ]; then #create keyfile if it does not exist
    new_keyfile_directory=$(dirname $new_keyfile)
    echo "$new_keyfile needs to exist for crypttab to open and mount container on boot"
    if ! [ -e "$new_keyfile_directory" ]; then
        echo "$new_keyfile_directory does not exist, creating"
        mkdir -p "$new_keyfile_directory"
        check_previous mkdir -p "$new_keyfile_directory"
    fi
    echo "creating $new_keyfile"
    ssh-keygen -t rsa -N "" -C "$date_time automated key creation, luks containers" -f $new_keyfile -b 4096
    check_previous "failed to create $new_keyfile"
    logger -p info "$0 created keyfile $new_keyfile"    
    check_previous logger -p info $0 created keyfile $new_keyfile  
fi

#back up /etc/crypttab
echo "backing up /etc/crypttab as /etc/crypttab.${date_time}"
sudo cp /etc/crypttab /etc/crypttab.${date_time}
check_previous "ERROR sudo cp /etc/crypttab /etc/crypttab.${date_time}"

trash_file="$0.trash"

while read i; do

        disk=$(echo $i | awk '{print $2}')
        old_keyfile=$(echo $i | awk '{print $3}')
    
    if [ ! -e $old_keyfile ]; then
        echo "original keyfile : $old_keyfile in /etc/crypttab does not exist"
        exit 1
    fi
        
        if  echo $i | awk '{print $4}' | grep "luks" &> /dev/null; then
                #finds all key slots currently in use, cuts to just get the number
                cryptsetup luksDump $disk | grep "ENABLED" | cut -d " " -f 3 | sed 's/://' | while read line; do 
                        array[$line]=$line
                        echo "${array[$line]}" 2>&1 >> $trash_file
                        check_previous "ERROR echo "${array[$line]}" 2>&1 >> $trash_file"
                
                done

                if [[ $(cat $trash_file | wc -l) -gt 7 ]]; then
                        echo "no slots available for $disk"
                        exit 1
                fi
        
                echo "adding $new_keyfile to $disk"
                if [ $old_keyfile == "none" ]; then
                        echo "Enter the password for the luks container: "
                        read -s password < /dev/tty #yeah... while loops are smrt.
                        
                        sudo cryptsetup luksAddKey $disk $new_keyfile <<< $password
                        check_previous "ERROR sudo cryptsetup luksAddKey $disk $new_keyfile"
                else
                        sudo cryptsetup luksAddKey $disk $new_keyfile --key-file $old_keyfile #add new keyfile
                        check_previous "ERROR sudo cryptsetup luksAddKey $disk $new_keyfile --key-file $old_keyfile"
                fi

                echo "$i" | sed -e "s@${old_keyfile}@${new_keyfile}@" >> $0.crypttab.new
                check_previous "ERROR: sed -e "s@${old_keyfile}@${new_keyfile}@" >> $0.crypttab.new"

        if [ $delete_flag == 1 ]; then        
                        for line2 in $( <${trash_file}); do
                                sudo cryptsetup luksKillSlot $disk $line2 --key-file $new_keyfile
                                check_previous "ERROR sudo cryptsetup luksKillSlot $disk $slot --key-file $new_keyfile"
                        done
                                
                fi
        
                if [ -e "$trash_file" ]; then #remove if trash file exists
                        rm -f $trash_file
                        check_previous "ERROR rm -f $trash_file"
                fi
                
                ln=$(grep -n "$i" /etc/crypttab | cut -d ":" -f1) #current line number
                
                if ! [[ $ln =~ ^[-+]?[0-9]+$ ]]; then #check if ln returns multiple lines
                        echo "$ERROR ln failed or returned multiple line entries"
                        exit 1
                fi
                
                sed -i "${ln} d" /etc/crypttab
                check_previous "ERROR sed -i "${ln} d" /etc/crypttab"
        fi
done < "/etc/crypttab"

#need to add checks to make sure an invalid key isn't removed...
if [ -e $0.crypttab.new ] && [ -s $0.crypttab.new ]; then
        echo "added the following entries"
        cat $0.crypttab.new | tee -a /etc/crypttab
        check_previous "ERROR cat $0.crypttab.new | tee -a /etc/crypttab"
        rm -f $0.crypttab.new
        check_previous "ERROR rm -f $0.crypttab.new"
else
        echo "$0.crypttab.new " 
fi
