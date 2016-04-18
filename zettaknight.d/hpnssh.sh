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

set -e #exit when an error is encountered

#source helper functions
running_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
setopts="${running_dir}/setopts.sh"
source $setopts || { echo "failed to source $setopts"; exit 1; }


################# default args ####################
###################################################
install_dir="/usr/local"
conf_dir="/etc/hpnssh"
w1="https://www.psc.edu/index.php/hpn-ssh-patches/hpn-14-kitchen-sink-patches/finish/24-hpn-14-kitchen-sink-patches/102-openssh-6-3p1-hpnssh14v2-kitchen-sink-patch/openssh-6.3p1-hpnssh14v2.diff.gz"
w2="http://openbsd.mirrors.hoobly.com/OpenSSH/portable/openssh-6.3p1.tar.gz"
w1_file="hpnssh_source"
w2_file="openssh_source"
dump_dir="${install_dir}/hpnssh_script_trash_output_delete_if_you_see_this"
hpnssh_source="${dump_dir}/${w1_file}"
openssh_source="${dump_dir}/${w2_file}"
d2_name="${dump_dir}/${openssh_source}_dir"
##################################################
##################################################

#setopts var "-d|--install_dir" "install_dir" "directory to install ssh [default: $install_dir]"
setopts var "-s|--openssh_source" "openssh_source" "full path to openssh source i.e [/tmp/openssh-6.3p1.tar.gz], default will download from the internet"
setopts var "-p|--patch" "hpnssh_source" "full path to hpnssh source patch archive i.e [/tmp/openssh-6.3p1-hpnssh14v2.diff.gz], default will download from the internet"
setopts var "-n|--port_num" "port_num" "defines the port number for ssh to be listening on"
setopts flag "-r|--replace" "replace_flag" "replace ssh in /etc/ssh instead of installing alongside"
setopts flag "-h|--help" "help_flag" "setting flag will show the help function"


if [[ -z "$install_dir" ]] || [[ -z "$openssh_source" ]] || [[ -z "$hpnssh_source" ]] || [[ $help_flag == 1 ]]; then
    show_help
    exit 1
fi

if [[ $replace_flag == 1 ]]; then
    port_num=22
else
    if [[ -z "$port_num" ]]; then
        echo -e "\nWARNING: ssh port is required if configuration is not to be overwritten\n"
        show_help
        exit 1
    fi
fi


if [ ! -d "$dump_dir" ]; then
    mkdir -p "$dump_dir"
fi

trap "{ echo ctrl+c : interrupt, deleting $dump_dir; if [ -d $dump_dir ]; then rm -rf $dump_dir; fi; }" INT

if [[ $replace_flag == 1 ]]; then
    conf_dir="/etc/ssh"
    install_dir="/usr"
fi

yum install zlib zlib-devel openssl openssl-devel gcc patch make -y 

#optional if -with-PAM is specified in ./configure
#yum install pam -y 
#yum install pam-devel -y 


if [[ ! -s "$openssh_source" ]] || [[ ! -s "$hpnssh_source" ]]; then
    echo -e "\ngrabbing the openssh and hpn-ssh sources..."
    cd "$dump_dir" && wget --output-document=${w1_file} $w1
    cd "$dump_dir" && wget --output-document=${w2_file} $w2
fi

#tar -xvf ${install_dir}/${hpnssh_source}
mkdir -p "$d2_name"
tar -xv --strip-components=1 -f "${openssh_source}" -C "$d2_name"

cd "$d2_name"
zcat "$hpnssh_source" | patch -p1
./configure --prefix=${install_dir} --sysconfdir=${conf_dir}
make
make install

#change port number for listening
if [ ! -z "$port_num" ]; then
    echo -e "\ninjecting information in ${conf_dir}/sshd_config"
    sed -i.bak "s/#Port 22/Port ${port_num}/g" ${conf_dir}/sshd_config
    sed -i "s@#PidFile /var/run/sshd.pid@PidFile /var/run/hpnsshd.pid@g" ${conf_dir}/sshd_config
fi

if [[ ! $replace_flag == 1 ]]; then
    cp /etc/init.d/sshd /etc/init.d/hpnsshd
    sed -i s@/usr/@${install_dir}/@g /etc/init.d/hpnsshd
    sed -i s@/etc/ssh/@${conf_dir}/@g /etc/init.d/hpnsshd
    sed -i s@sshd.pid@hpnsshd.pid@g /etc/init.d/hpnsshd
    echo -e "\ncreated /etc/init.d/hpnsshd"
fi

echo -e "\nstarting ssh"
if [[ $replace_flag == 1 ]]; then
    service sshd start
else
    service hpnsshd start
fi

if service sshd status || service hpnsshd status; then
    echo "succesfully started hpn-ssh"
    if lsof -i :${port_num}; then
        echo -e "\nCOMPLETE: ssh appears to be listening on ${port_num}, you may need to create firewall exceptions"
    else
        echo -e "\nssh isn't listening on $port_num"
    fi
else
    echo "failed to start hpn-ssh"
fi

############## remove install files###############
##################################################
if [ -d "$dump_dir" ]; then
    echo -e "\nremoving dir $dump_dir"
    rm -rf "$dump_dir"
fi
##################################################
##################################################
