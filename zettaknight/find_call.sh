function find_call () {

    local call=$1
    local var_declare=$2 #what variable name you would like to set the call in $1 to be
    local need_sudo=$3 #if the user is not root, will it need sudo?

    local path=("/usr/local/sbin" "/usr/local/bin" "/sbin" "/bin" "/usr/sbin" "/usr/bin" "/root/bin")
    local found_flag=0


    for loc in ${path[@]}; do
        local full_path="${loc}/${call}"
        if [ $found_flag == 0 ]; then
            if [ -x $full_path ]; then
                #echo -e "${call}=${full_path}"
                found_flag=1

                if [ -z "$var_declare" ]; then
                    local final_call="$call"
                else
                    local final_call="$var_declare"
                fi

                if ! [ -z "$need_sudo" ]; then #if user is not root append sudo to each command
                    if [ $(id -u) != 0 ]; then
                        local full_path="sudo "${full_path}
                    fi
                fi

                eval $final_call"=\"\$full_path\""

            fi
        fi
    done


    if [ $found_flag == 0 ]; then
        echo -e "call $call not found, cannot continue"
        exit 1
    fi
}
