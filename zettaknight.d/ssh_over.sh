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
function ssh_over () {
    ssh_cmd="$@"
    
    if [ -z "$ssh" ]; then
        ssh=$(which ssh)
        if [ -x "$ssh" ]; then
            ssh="/bin/ssh"
        fi
    fi
    
    if [ -z "$remote_ssh" ]; then
        echo "variable remote_ssh is required for function ssh_over, not set"
        exit 1
    fi
    
    if ! [[ -z "$identity_file" ]]; then
        if [[ -f "$identity_file" ]]; then
            $ssh -q -i "$identity_file" "$remote_ssh" "$ssh_cmd"
        else
            echo "$identity_file is not accessible, cannot use"
            $ssh -q $remote_ssh "$ssh_cmd"
        fi
    else
        $ssh -q $remote_ssh "$ssh_cmd"
    fi

}
