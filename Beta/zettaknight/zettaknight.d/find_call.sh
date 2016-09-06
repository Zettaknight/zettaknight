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
