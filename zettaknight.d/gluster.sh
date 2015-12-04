#!/bin/bash

#intended to be used with Oracle Linux / Fedora
#    ssh_over wget -P /etc/yum.repos.d http://download.gluster.org/pub/gluster/glusterfs/LATEST/EPEL.repo/glusterfs-epel.repo
#    ssh_over yum install glusterfs-server -y

function show_help () {
cat << EOF
version $version

    DESCRIPTION:
		$(basename $0) used to monitor zfs systems, checks multipath, xinted, and
		zpool health check.

		This utility is intended to be run as a regularly scheduled cron job and
		must be run as root.

    $setopts_help
EOF
}

function ssh_over () {
    ssh_cmd="$@"

    #if [ $(id -u) != 0 ]; then
    #    ssh="/bin/ssh -t"

    if [ -z "$identity_file" ]; then
        $ssh -q $remote_ssh "$ssh_cmd"
    else
        $ssh -q -i $identity_file $remote_ssh "$ssh_cmd"
    fi

}

### necessary things ##########
set -o nounset || set -u #error on unbound variables
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
g_vol_name="gv0" #name of the gluster volume
g_num_nodes=2 #number of nodes a file will be on at any one time, cannot be greater than available nodes
master_node="$(hostname -f)"
###############################


##### setopts config ##########
setopts var "-m|--master" "master_node" "master node name if different than fdqn"
setopts var "-s|--slave" "nodes" "slave nodes for gluster configuration"
setopts flag "-f|--firewall-exceptions" "firewall_flag" "flag to add exceptions for all gluster nodes in iptables"
###############################



#check if g_nodes is greater than servers
if [ $( $(( ${#nodes[@]} + 1 )) ) -lt $g_num_nodes ]; then # +1 for the master node not defined in nodes
    echo "not enough nodes defined to allow $g_num_nodes concurrent copies"
    exit 1
fi

#configure firewall exceptions
dont_add_twice=0 #don't add the master node multiple times if more than 1 node is specified
for server in ${nodes[@]}; do
    #install gluster
    remote_ssh="root@${server}"
    remote_host="$(echo $remote_ssh | cut -d "@" -f 2)"
    
    echo -e "\nconfiguring $remote_host"
    ssh_over service glusterd start
    
    if [ $firewall_flag == 1 ]; then
        #add iptables excpetions for servers
        
        if [ $dont_add_twice != 0 ]; then
            echo "[iptables] adding exception for $server"
            iptables -C INPUT -p all -s $master_node -j ACCEPT
            dont_add_twice=1
        fi
        
        echo "[iptables] adding exception for $server"
        iptables -C INPUT -p all -s $server -j ACCEPT
    fi
done

gluster peer probe "$server" #only on the master
gluster volume create $g_vol_name replica $g_num_nodes 
gluster volume create gv0 replica 2 mc-tst-c-02.server.clemson.edu:/test_crypt/gluster/vol mc-tst-c-03.server.clemson.edu:/test_crypt/gluster/vol

echo -e "completed info for gluster volume $g_vol_name"
gluster volume info

echo -e "starting gluster volume"
gluster volume start $g_vol_name
