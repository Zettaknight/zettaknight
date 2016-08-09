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
# Import python libs

import os
import shutil
import sys
import zettaknight_globs
import zettaknight_utils
import zettaknight_zfs

#redo of the notes section since codeanywhere doesn't want to save anything
'''
check/create local zpool
    check/create local datasets, if already defined in conf file
        check/create zettaknight share
    if luks
        check/create header backups
        
create config file
    create defaults section
    if no datasets, prompt to create first dataset
    
 
if remote
    check/create ssh key auth
    check/create remote zpool
        if luks
            check/create header backups
 
'''
 
def first_step():
    ret = {}
    arg_dict = {}
    
    try:
        
        pool_name = "zfs_data" #default pool name 
        arg_dict["pool_name"] = pool_name
        
        ret[pool_name] = {}
        
        ############### creation of the zpool ################
        ######################################################
        
        #test if a zpool exists
        zpool_list_cmd = "/sbin/zpool list -H"
        zpool_list_run = zettaknight_utils.spawn_job(zpool_list_cmd)
        chk_code, chk_msg = zpool_list_run.popitem()
        if int(chk_code) != 0: #if zpool list -H returns empty
            #query_return_item is defined in zettaknight_utils
            create_pool_question = zettaknight_utils.query_yes_no("No pool detected, would you like to create one?")
            if create_pool_question:
                arg_dict["disk_list"] = zettaknight_utils.query_return_item("File containing all list of disks to be used for {0}, I.E /tmp/bunchofdisks.txt: ".format(pool_name))
                arg_dict["raid"] = zettaknight_utils.query_return_item("Raid level to be used [1-3]. I.E. 4+1, 5+2, 1+1: ")
                arg_dict["ashift"] = zettaknight_utils.query_return_item("ashift value for {0}, value is 9 for 512 block disks and 12 for 4096 block disks: ".format(pool_name))
                arg_dict["luks"] = zettaknight_utils.query_yes_no("encrypt data disks with LUKS? ")
        
                print("creating zpool: {0}".format(pool_name))
                create_output = zettaknight_zpools.create(pool_name, **arg_dict) #from zettaknight_zpools
            #ret[pool_name]['Zpool Create'] = create_output[pool_name]['Zpool Create'] #'NoneType' object has no attribute '__getitem__'
        else:
            print("a pool already exists, moving on")
        ######################################################
        ######################################################
        
        ################## ssh key creation  #################
        print("checking for {0}".format(zettaknight_globs.identity_file))
        if not os.path.isfile(zettaknight_globs.identity_file):
            print(zettaknight_utils.printcolors("zettaknight id file not found, generating.", "WARNING"))
            keygen_output = zettaknight_utils.ssh_keygen(zettaknight_globs.identity_file)
            ret[pool_name]['Generate SSH Keygen'] = keygen_output[zettaknight_globs.fqdn]['Generate SSH Key']
        else:
            print("{0} exists, moving on".format(zettaknight_globs.identity_file))
        ######################################################
        
        ############# backup luks headers ####################
        print("backing up luks headers for {0}".format(pool_name))
        luks_backup_output = zettaknight_utils.backup_luks_headers()
        ret[pool_name]['Backup Luks Headers'] = luks_backup_output[zettaknight_globs.fqdn]['Backup Luks Headers']
        ######################################################
        
        
        ######## create zettaknight configuration file #######
        if not os.path.isdir(zettaknight_globs.conf_dir_new): #if new directory does not exists, make it
            print("creating {0}".format(zettaknight_globs.conf_dir_new))
            os.mkdir(zettaknight_globs.conf_dir_new)
        ######################################################
        
        ########### create zettaknight store #################
        ######################################################
        if not os.path.isdir("/{0}".format(zettaknight_globs.zettaknight_store)):
            dataset_check_run = zettaknight_utils.pipe_this2("/sbin/zfs list -H | grep {0}".format(zettaknight_globs.zettaknight_store))
            if int(dataset_check_run.returncode) != 0:
                print("creating configuration file for {0}".format(zettaknight_globs.zettaknight_store))
                zettaknight_utils.create_config(dataset=zettaknight_globs.zettaknight_store)
                
        gerp_run = zettaknight_utils.pipe_this2("/sbin/zfs list -H | /bin/grep {0}".format(zettaknight_globs.zettaknight_store))
        if int(gerp_run.returncode) is not 0:
            zettaknight_zfs.add_dataset(zettaknight_globs.zettaknight_store)
        
        
        #backup files to store
        files = ["/etc/exports", "/etc/crypttab", "{0}".format(zettaknight_globs.config_file_new)]
        for file in files:
            if os.path.exists(file):
                destination_dir = "/{0}/{1}".format(zettaknight_globs.zettaknight_store, zettaknight_globs.fqdn) #add leading slash, zfs_share defined
                filename = file.replace("/", "") #remove illegal characters from file path and save file as the concatenated version
                if not os.path.isdir(destination_dir):
                    os.mkdir(destination_dir)
                print("backing up {0} to {1}".format(file, destination_dir))
                shutil.copyfile(file, "{0}/{1}".format(destination_dir, filename))
        ######################################################
        ######################################################
        
        ############ create the first dataset ################
        dataset = zettaknight_utils.query_return_list("Datasets to be created on {0}: ".format(pool_name))
        for item in dataset:
            dset_args = []
            dataset_full = "{0}/{1}".format(pool_name, item)
            dset_args.append(dataset_full)
            dset_args.append("create_config=True")
            add_dset_output = zettaknight_zfs.add_dataset(*dset_args) #from zettaknight_utils
            ret[pool_name]['Add dataset {0}'.format(dataset_full)] = add_dset_output[dataset_full]['add_dataset']
        ######################################################
        
        ###### create server to server transfer pathing ######
        replication_output = zettaknight_zfs.configure_replication() #from zettaknight_zfs
        for repl_job, repl_job_output in replication_output[dataset_full].itervalues():
            ret[pool_name]['{0}'.format(repl_job)] = repl_job_output
        ######################################################
    
    except Exception as e:
        print(zettaknight_utils.printcolors(e, "FAIL"))
        sys.exit(1)
    
    zettaknight_globs.zfs_conf = _get_conf()
    
    return ret
