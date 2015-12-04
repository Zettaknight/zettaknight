#!/usr/bin/python
# -*- coding: utf-8 -*-
# Import python libs

import socket
import os
import datetime

#zettaknight's current version
version = "0.0.5" 

#version of python required by zettaknight
required_python_version = "2.x"

#if no contact information is provided within the configuration file
#zettaknight will contact this/these address(es) by default
#multiple entires should be separated by a space
default_contact_info = "mcarte4@g.clemson.edu rgoodbe@g.clemson.edu"

#variable to determine the fully qualified domain name of the system
fqdn = socket.getfqdn()

#determines the current date
today_date = str(datetime.datetime.today().strftime('%Y%m%d_%H%M'))

#the following sets the directory this file is in as the base for where all
#other files necessary for zettaknight are referenced

abspath = os.path.realpath(__file__)
base_dir = os.path.dirname(abspath)
script_dir = os.path.dirname("{0}/zettaknight.d/".format(base_dir))
conf_dir = os.path.dirname("{0}/zettaknight.conf.d/".format(base_dir))

#############################################################################################
#############################################################################################

#crypt_dir stores the ssh key used for both luks encryption and ssh transfers between servers
#two options are available below, one is root and the other within zettaknight's operating directory

#crypt_dir = os.path.dirname("{0}/.zettaknight.crypt/".format(base_dir))
crypt_dir = "/root/.ssh/.zettaknight_crypt"

#the identity file is the name of the key used for luks and ssh communication for zettaknight
identity_file = "{0}/zettaknight.id".format(crypt_dir)

#############################################################################################
#############################################################################################

#the config file is a yaml file used in all processes of zettaknight.  This sets the configuration
#on which zettaknight does it automated processes.

config_file = "{0}/{1}.conf".format(conf_dir, fqdn)

#############################################################################################
#############################################################################################


#the following are locations for scripts that zettaknight uses for various processes

snap_script = "{0}/zfs_snap.sh".format(script_dir)
cleanup_script = "{0}/zfs_cleanup_snaps.sh".format(script_dir)
quota_script = "{0}/zfs_quota.sh".format(script_dir)
luks_key_script = "{0}/luks_key_manage.sh".format(script_dir)
luks_header_backup_script = "{0}/luks_header_backup.sh".format(script_dir)
ssh_keygen_script = "{0}/ssh_keygen.sh".format(script_dir)
zfs_nuke_script = "{0}/zfs_nuke.sh".format(script_dir)
zpool_create_script = "{0}/zfs_zpool_create.sh".format(script_dir)
mail_out_script = "{0}/mail_out.sh".format(script_dir)
update_cron_script = "{0}/update_cron.sh".format(script_dir)
zfs_monitor_script = "{0}/zfs_monitor.sh".format(script_dir)

#############################################################################################
#############################################################################################

#default flags for varius functions in zettaknight's entry_point

mail_flag = False
mail_error_flag = False
nocolor_flag = False

#############################################################################################
#############################################################################################

zfs_conf = {}