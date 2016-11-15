#!/bin/bash

#set -x
#shopt -s failglob

#source helper functions
running_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
setopts="${running_dir}/setopts.sh"

source $setopts || { echo "failed to source $setopts"; exit 1; }

zfs="/sbin/zfs"


function show_help () {
cat <<EOF

version $version

USAGE:
$0 [fdzco]

DESCRIPTION:
        $(basename $0) is used to restore files or directories in zfs filesystems.

OPTIONS:
        -d directory where listed files are located
        -f files to be retrieved from directory listed in -d, if -f is empty but -d is declared, script assumes the entire directory should be restored
        -z zfs dataset defined on the box, this option keeps the script from having to search, saving time
        -r remote directory location for luks header backups
        -o if file is greater than specified days old, do not recover
        -c flag to tell the script to md5 checksum a the restore file if the destination file exists.  Copy with .R extension if difference, do nothing if the same
        -h Shows this help dialogue.
EOF
}



#setopts var "-f|--files" "files" "files to be retrieved from directory listed in -d, if -f is empty but -d is declared, script assumes the entire directory should be restored"
#setopts var "-d|--directory" "dataset" "directory where listed files are located"
#setopts var "-z|--dataset" "final_dataset" "zfs dataset defined on the box, this option keeps the script from having to search, saving time"
#setopts var "-o|--days" "days_old" "if file is greater than specified days old, do not recover"
#setopts flag "-c|--checksum" "checksum_flag" "flag to tell the script to md5 checksum a the restore file if the destination file exists.  Copy with .R extension if difference, do nothing if the same"
#setopts flag "-h|--help" "display_help_flag" "Shows this help dialogue."



while getopts "f:d:z:co:?" OPTION
do
     case $OPTION in
        f)
            files=$OPTARG
            echo "files argument is $files"
            ;;
        d)
            dataset=$OPTARG
            case $dataset in
                /*) ;;
                *) dataset="/${dataset}";;
            esac
            ;;
        z)
            final_dataset=$OPTARG
            case $final_dataset in
                /*) final_dataset=${final_dataset#'/'};;
                *) ;;
            esac
            ;;
        c)
            checksum_flag=1
            ;;
        o)
            days_old=$OPTARG
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


if [ -z "$dataset" ]; then

    echo "required arguments missing, missing -d"
    show_help
    exit 1
    
fi

if [ -z "$days_old" ]; then

    days_old=999999 #set a farsical days old number if not specified

fi


###################### find the zfs dataset in the path given #########################
#######################################################################################


if [[ -z "$final_dataset" ]]; then

    defined_datasets=$(zfs list -o name -H)
    found_flag=0

    case $dataset in
            /*) ;;
            *) dataset="/${dataset}";;
    esac


    zfs_dataset="$dataset"

    case $zfs_dataset in
            *) ;;
            /*) zfs_dataset=$(echo "${dataset}" | sed -e 's@^/@@');;
    esac


    while [[ "$zfs_dataset" != "." ]]; do

        if [[ $found_flag != 0 ]]; then
    
            break
    
        fi

        for defined_dataset in $defined_datasets; do

            if [ "$defined_dataset" == "$zfs_dataset" ]; then
        
                if [[ $found_flag == 0 ]]; then
    
                    final_dataset="$zfs_dataset"
                    echo "determined zfs dataset is $final_dataset"
                    found_flag=1
                    break
                
                fi
    
            fi

        done
    
        zfs_dataset=$(dirname "$zfs_dataset")
    
    done

    if [ "$zfs_dataset" == "." ]; then
        
            echo "no zfs dataset can be found in $dataset, script must exit"
            exit 1
        
    fi
    
fi

#######################################################################################
#######################################################################################


################ search snapshots for file/dir ########################################
#######################################################################################


#get the reverse order of snaps, newest snapshot first
snapshots=$(zfs list -t snapshot -o name -H | grep "$final_dataset" | awk -F '@' '{print $NF}' | sort -r -n)

if [[ -z "$files" ]]; then
    #if no files given, get all directory

    echo "haven't done this yet"
    
else

    unset restored_files
    declare restored_files

    #if files, go get those files
    for file in $files; do
    
        found_flag=0
        
        echo -e "\nlooking for file [$file]"
        
        for snapshot in $snapshots; do
            
            #echo -e "\tlooking in snapshot [$snapshot]"
        
            restore_from_dir=$(echo "$dataset" | sed -e "s@${final_dataset}@${final_dataset}/.zfs/snapshot/${snapshot}@")
            
            glob_expand=$(echo ${restore_from_dir}/${file})
            
            for f in $glob_expand; do
            
                if [[ -e "${f}" ]]; then
            
                    found_flag=1
                    restored_file=$(echo "$f" | awk -F '/' '{print $NF}')
                    
                    if ! [[ " ${restored_files[@]} " =~ " ${restored_file} " ]]; then
                        
                        if [ ! -e "${dataset}/${f}" ] && [ ! -e "${dataset}/${f}.R" ]; then
                        
                            file_mtime=$(stat -c %Y $f)
                            curr_time=$(date +%s)
                            file_days=$(( (currtime - filemtime) / 86400 ))
                            
                            if [[ "$file_days" -ge "$days_old" ]]; then
                            
                                echo "file [ $f ] is older than $days_old day(s), will not restore"
                                
                            else
                        
                                cp "$f" "${dataset}/$restored_file.R"
                                
                                if [ $? -eq 0 ]; then
                                
                                    echo -e "\t[SUCCESS] file ${dataset}/$restored_file.R recovered from snapshot $snapshot"
                                    restored_files+=("$restored_file")
                                    
                                else
                                
                                    echo -e "\t[FAILURE] file ${dataset}/$restored_file.R failed to recover from snapshot $snapshot"
                                    restored_files+=("$restored_file")
                                    
                                fi
                                
                            fi
                            
                        else
                        
                            echo -e "\t[WARNING] file [ ${dataset}/${f} ] already exists or has already been recovered, will not overwrite"
                            restored_files+=("$restored_file")
                        
                        fi                    
                            
                    fi
                        
                fi
                        
            done

        done
            
        if [[ $found_flag == 0 ]]; then
    
            echo -e "\t[WARNING] cannot find file [ $file ] in any snapshot, please verify filename"
    
        fi

    done

fi
