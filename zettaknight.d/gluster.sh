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

#intended to be used with Oracle Linux / Fedora
#    ssh_over wget -P /etc/yum.repos.d http://download.gluster.org/pub/gluster/glusterfs/LATEST/EPEL.repo/glusterfs-epel.repo
#    ssh_over yum install glusterfs-server -y
#firewall exception needed
#iptables -C INPUT -p all -s $server -j ACCEPT


#source helper functions
running_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
setopts="${running_dir}/setopts.sh"
source $setopts || { echo "failed to source $setopts"; exit 1; }

function show_help () {
cat << EOF
version $version

    DESCRIPTION:
        $(basename $0) is used to deploy a gluster cluster.

    $setopts_help
EOF
}

function ssh_over () {
    ssh_cmd="$@"

    #if [ $(id -u) != 0 ]; then
    #    ssh="/bin/ssh -t"

    if [ -z "$identity_file" ]; then
        ssh -q $remote_ssh "$ssh_cmd"
    else
        ssh -q -i $identity_file $remote_ssh "$ssh_cmd"
    fi

}

function create_array_from_string () {
    local string="$1"
    local array_name="$2"
    local i=0

    for item in $string; do
        eval $array_name[$i]="$item"
        i=$(($i + 1))
    done

}


### necessary things ##########
#set -o nounset || set -u #error on unbound variables
set -o errexit || set -e #exit if any error is encountered
set -o pipefail #make sure each output in pipestatus is checked, not just the final return
###############################

### vars ######################
#source helper functions
running_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
setopts="${running_dir}/setopts.sh"
source $setopts || { echo "failed to source $setopts"; exit 1; }

master_node="len016.zfs-snap.clemson.edu"
#nodes=("len063.zfs-snap.clemson.edu") #all nodes to be used in gluster config other than the node executing the script
g_vol_name="gv0" #defalut name of the gluster volume
g_num_nodes=2 #number of nodes a file will be on at any one time, cannot be greater than available nodes
master_node="$(hostname -f)"
default_gluster_vol_name="gv0"
user="root"
###############################


##### setopts config ##########
setopts var "-m|--mount_point" "g_mnt_point" "where the gluster volume gets mounted"
setopts flag "-f|--firewall-exceptions" "firewall_flag" "flag to add exceptions for all gluster nodes in iptables"
setopts var "-v|--vips" "vips" "dont' really know what to write here ATM"
setopts var "-n|--name" "g_vol_name" "name of the gluster volume, default is $g_vol_name"
setopts var "-p|--peers" "g_peers" "names of the boxes to be used with gluster"
setopts var "-u|--user" "user" "username to configure each peer over ssh, default is root"
###############################

######### tests ###############
if [[ -z "$g_mnt_point" ]] || [[ -z "$g_peers" ]]; then
    echo " required arguments missing"
    show_help
    exit 1
fi

###############################



#check if g_nodes is greater than servers
create_array_from_string "$g_peers" "array_peers"

#if [[ ${array_peers[$#]} -lt $g_num_nodes ]]; then # +1 for the master node not defined in nodes
#    echo "not enough nodes defined to allow $g_num_nodes concurrent copies"
#    exit 1
#fi
    
echo "\ndefining peer list"
for server in "$g_peers"; do
    gluster peer probe "$server" #only on the master
    
    #build server argument for gluster volume creation outside loop
    if [[ -z "$server_string" ]]; then
        server_string="${server}:${g_mnt_point}"
    else
        server_string="${server}:${g_mnt_point} $server_string"
    fi
done
 
gluster volume create $g_vol_name replica $g_num_nodes $server_string force

echo -e "\ncompleted info for gluster volume $g_vol_name"
gluster volume info

echo -e "\nstarting gluster volume"
gluster volume start $g_vol_name
