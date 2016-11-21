#!/usr/bin/python
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
# -*- coding: utf-8 -*-

###############################################################################################
################## DO NOT MODIFY ANYTHING BELOW THIS LINE #####################################
###############################################################################################






# Import python libs
import socket
import os
import datetime


#zettaknight's current version
version = "0.1"

#version of python required by zettaknight
required_python_version = "2.x"

#variable to determine the fully qualified domain name of the system
fqdn = socket.getfqdn()

#needs to be removed when order YAML dict is in place
pool_name = "zfs_data"

#zfs dataset definition for store information for zettaknight, config files and keys will reside here
zettaknight_store = "{0}/zettaknight/{1}".format(pool_name, fqdn)

#determines the current date
today_date = str(datetime.datetime.today().strftime('%Y%m%d_%H%M'))
today_date2 = str(datetime.datetime.today().strftime('%Y%m%d'))

#the following sets the directory this file is in as the base for where all
#other files necessary for zettaknight are referenced

abspath = os.path.realpath(__file__)
base_dir = os.path.dirname(abspath)
script_dir = os.path.dirname("{0}/zettaknight.d/".format(base_dir))
conf_dir = os.path.dirname("{0}/zettaknight.conf.d/".format(base_dir))
conf_dir_new = os.path.dirname("/etc/zettaknight/")
#conf_dir_final = os.path.dirname("/{0}".format(zettaknight_store)) #add leading slash, zfs share

#############################################################################################
#############################################################################################

#crypt_dir stores the ssh key used for both luks encryption and ssh transfers between servers
#two options are available below, one is root and the other within zettaknight's operating directory

#crypt_dir = os.path.dirname("{0}/.zettaknight.crypt/".format(base_dir))
crypt_dir = "/root/.ssh/.zettaknight_crypt"
luks_header_dir = "{0}/luks_header_backups".format(crypt_dir)

#the identity file is the name of the key used for luks and ssh communication for zettaknight
identity_file = "{0}/zettaknight.id".format(crypt_dir)

#############################################################################################
#############################################################################################

#the config file is a yaml file used in all processes of zettaknight.  This sets the configuration
#on which zettaknight does it automated processes.

default_config_file = "{0}/default_conf_file.yml".format(conf_dir)
config_file = "{0}/{1}.conf".format(conf_dir, fqdn)
config_file_new = "{0}/{1}.conf".format(conf_dir_new, fqdn)

default_pool_config_file = "{0}/default_pool_conf_file.yml".format(conf_dir)
pool_config_file = "{0}/{1}_zpool.conf".format(conf_dir_new, fqdn)

default_zettaknight_config_file = "{0}/default_zettaknight_conf_file.yml".format(conf_dir)
zettaknight_config_file = "{0}/zettaknight.conf".format(conf_dir_new)

#cron.d files
crond_primary = "/etc/cron.d/{0}_primary_datasets".format(fqdn)
crond_secondary = "/etc/cron.d/{0}_secondary_datasets".format(fqdn)
crond_zettaknight = "/etc/cron.d/zettaknight"

#stats file
zpool_perf_dir = "/{0}/zettaknight_stats".format(zettaknight_store)
zpool_iostat_file = "{0}/{1}_zpool_iostat_file".format(zpool_perf_dir, today_date2)

#mtime file
mtime_file = "/{0}/zettaknight_mtime_{1}".format(zettaknight_store, fqdn)
zpool_mtime_file = "/{0}/zettaknight_zpool_mtime_{1}".format(zettaknight_store, fqdn)

#############################################################################################
#############################################################################################


#the following are locations for scripts that zettaknight uses for various processes

snap_script = "{0}/zfs_snap.sh".format(script_dir)
cleanup_script = "{0}/zfs_cleanup_snaps.sh".format(script_dir)
cleanup_remote_script = "{0}/zfs_cleanup_remote_snaps.sh".format(script_dir)
quota_script = "{0}/zfs_quota.sh".format(script_dir)
luks_key_script = "{0}/luks_key_manage.sh".format(script_dir)
luks_header_backup_script = "{0}/luks_header_backup.sh".format(script_dir)
ssh_keygen_script = "{0}/ssh_keygen.sh".format(script_dir)
zfs_nuke_script = "{0}/zfs_nuke.sh".format(script_dir)
zpool_create_script = "{0}/zfs_zpool_create.sh".format(script_dir)
mail_out_script = "{0}/mail_out.sh".format(script_dir)
update_cron_script = "{0}/update_cron.sh".format(script_dir)
zfs_monitor_script = "{0}/zfs_monitor.sh".format(script_dir)
cifs_share_script = "{0}/zfs_cifs_add_share.sh".format(script_dir)
sync_script = "{0}/sync.sh".format(script_dir)
hpnssh_script = "{0}/hpnssh.sh".format(script_dir)
perf_stats_script = "{0}/zfs_data_generator.sh".format(script_dir)
backup_snap_script = "{0}/snap_backup.sh".format(script_dir)

#default flags for varius functions in zettaknight's entry_point

mail_flag = False
mail_error_flag = False
nocolor_flag = False
help_flag = False
elapsed_time = 0

#default names for zpools and cifs/nfs datasets
cifs_dset_suffix = "cifs"
nfs_dset_suffix = "nfs"

#############################################################################################
#############################################################################################

zfs_conf = {}
zpool_conf = {}
zettaknight_conf = {}
