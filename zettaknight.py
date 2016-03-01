#!/usr/bin/python
# -*- coding: utf-8 -*-
# Import python libs

import sys
import yaml
import zettaknight_globs
import os
import shutil
import argparse
from zettaknight_zpool import *
from zettaknight_utils import *
from zettaknight_zfs import *
from zettaknight_recover import *
from zettaknight_ldap import *
from zettaknight_check import *

        
def argparsing():
    
    #parser = argparse.ArgumentParser()
    
    #parser.add_argument('function', metavar=('Function', 'F'), nargs='+', help='Zettaknight function to execute.')
    #parser.add_argument('-f', '--foo', nargs='+', help='just display something different')
    #parser.parse_args()
    
    
    return
    
def first_run():
    
    ret = {}
    arg_dict = {}
    
    try:
        
        pool_name = "zfs_data" #default pool name 
        arg_dict["pool_name"] = pool_name
        
        ret[pool_name] = {}
        
        ########## user input definitions ###################
        #query_return_item is defined in zettaknight_utils
        arg_dict["disk_list"] = query_return_item("File containing all list of disks to be used for {0}, I.E /tmp/bunchofdisks.txt: ".format(pool_name))
        arg_dict["raid"] = query_return_item("Raid level to be used [1-3]. I.E. 4+1, 5+2, 1+1: ")
        arg_dict["ashift"] = query_return_item("ashift value for {0}, value is 9 for 512 block disks and 12 for 4096 block disks: ".format(pool_name))
        arg_dict["luks"] = query_yes_no("encrypt data disks with LUKS? ")
        ######################################################
        
        
        print("arg_dict is {0}".format(arg_dict))
        
        ############### creation of the zpool ################
        print("creating zpool: {0}".format(pool_name))
        create_output = create(pool_name, **arg_dict) #from zettaknight_zpools
        #ret[pool_name]['Zpool Create'] = create_output[pool_name]['Zpool Create'] #'NoneType' object has no attribute '__getitem__'
        ######################################################
        
        ################## ssh key creation  #################
        print("checking for {0}".format(zettaknight_globs.identity_file))
        if not os.path.isfile(zettaknight_globs.identity_file):
            print(printcolors("zettaknight id file not found, generating.", "WARNING"))
            keygen_output = ssh_keygen(zettaknight_globs.identity_file)
            ret[pool_name]['Generate SSH Keygen'] = keygen_output[zettaknight_globs.fqdn]['Generate SSH Key']            
        ######################################################
        
        ############# backup luks headers ####################
        if arg_dict["luks"]:
            print("backing up luks headers for {0}".format(pool_name))
            luks_backup_output = backup_luks_headers()
            ret[pool_name]['Backup Luks Headers'] = luks_backup_output[zettaknight_globs.fqdn]['Backup Luks Headers']
        ######################################################
        
        
        ######## create zettaknight configuration file #######
        if not os.path.isdir(zettaknight_globs.conf_dir_new): #if new directory does not exists, make it
            print("creating {0}".format(zettaknight_globs.conf_dir_new))
            os.mkdir(zettaknight_globs.conf_dir_new)
        ######################################################
        
        ############ create the first dataset ################
        dataset = query_return_list("Datasets to be created on {0}: ".format(pool_name))
        for item in dataset:
            dset_args = []
            dataset_full = "{0}/{1}".format(pool_name, item)
            dset_args.append(dataset_full)
            dset_args.append("create_config=True")
            add_dset_output = add_dataset(*dset_args) #from zettaknight_utils
            ret[pool_name]['Add dataset {0}'.format(dataset_full)] = add_dset_output[dataset_full]['add_dataset']
        ######################################################
        
        ###### create server to server transfer pathing ######
        replication_output = configure_replication() #from zettaknight_zfs
        for repl_job, repl_job_output in replication_output[dataset_full].itervalues():
            ret[pool_name]['{0}'.format(repl_job)] = repl_job_output
        ######################################################
    
    except Exception as e:
        print(printcolors(e, "FAIL"))
        sys.exit(1)
    
    zettaknight_globs.zfs_conf = _get_conf()
    
    return ret

    
def _get_conf():
    '''
    '''
    config_dict = {}
    try:
        conff = open(zettaknight_globs.config_file_new, 'r')   
        config_dict = yaml.safe_load(conff)
    except Exception as e:
        print(printcolors("error opening {0}, checking old location: {1}".format(zettaknight_globs.config_file_new, zettaknight_globs.conf_dir), "WARNING"))
        try:
            if os.path.isfile(zettaknight_globs.config_file): #test if old config file exists
                if not os.path.isdir(zettaknight_globs.conf_dir_new): #if new directory does not exists, make it
                    os.mkdir(zettaknight_globs.conf_dir_new)
                    print(printcolors("created {0}".format(zettaknight_globs.conf_dir_new), "OKBLUE"))
                if not os.path.isfile(zettaknight_globs.config_file_new): #if new config file does not exist, move it to new location 
                    shutil.move(zettaknight_globs.config_file, zettaknight_globs.config_file_new)
                    print(printcolors("copied {0} to {1}".format(zettaknight_globs.config_file, zettaknight_globs.config_file_new, "OKBLUE")))
                    os.symlink(zettaknight_globs.config_file_new, zettaknight_globs.config_file)
                    print(printcolors("created symlink {0} --> {1}".format(zettaknight_globs.config_file_new, zettaknight_globs.config_file, "OKBLUE")))
            else:
                print(printcolors("file {0} does not exists".format(zettaknight_globs.config_file), "WARNING"))
            conff = open(zettaknight_globs.config_file_new, 'r')
            config_dict = yaml.safe_load(conff)
        except Exception as e:
            print(printcolors(e, "FAIL"))
            first_run_out = query_yes_no("conf file: {0} does not exist, would you like to create it?".format(zettaknight_globs.config_file_new))
            if first_run_out:
                first_run()
            else:
                pass
    
    #test to determine if pool and child objects are both defined in config_file
    defined_zpools = zettaknight_utils.spawn_job("/sbin/zpool list -o name -H")
    zpool_list = []

    for zpool in defined_zpools.itervalues():
        zpool_clean = zpool.strip()
        for dataset in config_dict.iterkeys():
            dataset_clean = dataset.strip()
            
            if zpool_clean == dataset_clean:
                #print("{0} == {1}").format(zpool_clean, dataset_clean)
                zpool_list.append(zpool_clean)

    #print(zpool_list)
    if zpool_list:
        for zpool in zpool_list:
            num = zettaknight_utils.pipe_this2("cat {0} | grep {1} | wc -l".format(zettaknight_globs.config_file, zpool))
            num_out = num.stdout.read()
            num_out = num_out.strip() #remove trailing newline
            if int(num_out) > 1:
                print(printcolors("pool {0} is defined with child objects, both cannot be defined\ncheck definitions in {1}".format(zpool, zettaknight_globs.config_file), "FAIL"))
                sys.exit(1)
    
    new_dict = {}
    #print(config_dict)
    for dataset in config_dict.iterkeys():
        if dataset != 'defaults':
            new_dict[dataset] = {}
        
            ########### define var ###############
            new_dict[dataset]['user'] = {}
            new_dict[dataset]['quota'] = {}
            new_dict[dataset]['refquota'] = {}
            new_dict[dataset]['reservation'] = {}
            new_dict[dataset]['refreservation'] = {}
            new_dict[dataset]['retention'] = {}
            new_dict[dataset]['secure'] = {}
            new_dict[dataset]['contact'] = {}
            new_dict[dataset]['snap'] = {}
            new_dict[dataset]['snap']['interval'] = {}
            new_dict[dataset]['snap']['remote_server'] = {}
            #####################################
        
            #print("dataset is {0}".format(dataset))
        
            ############## determine if there are any default values ##################
            ###########################################################################
            if 'defaults' in config_dict.iterkeys():
            
                if 'user' in config_dict['defaults'].iterkeys():
                    new_dict[dataset]['user'] = config_dict['defaults']['user']
                
                if 'quota' in config_dict['defaults'].iterkeys():
                    new_dict[dataset]['quota'] = config_dict['defaults']['quota']
                
                if 'refquota' in config_dict['defaults'].iterkeys():
                    new_dict[dataset]['refquota'] = config_dict['defaults']['refquota']
                
                if 'reservation' in config_dict['defaults'].iterkeys():
                    new_dict[dataset]['reservation'] = config_dict['defaults']['reservation']
                
                if 'refreservation' in config_dict['defaults'].iterkeys():
                    new_dict[dataset]['refreservation'] = config_dict['defaults']['refreservation']
                
                if 'retention' in config_dict['defaults'].iterkeys():
                    new_dict[dataset]['retention'] = config_dict['defaults']['retention']
                
                if 'secure' in config_dict['defaults'].iterkeys():
                    new_dict[dataset]['secure'] = config_dict['defaults']['secure']
                
                if 'contact' in config_dict['defaults'].iterkeys():
                    new_dict[dataset]['contact'] = config_dict['defaults']['contact']
                
                if 'snap' in config_dict['defaults'].iterkeys():
                    if 'interval' in config_dict['defaults']['snap'].iterkeys():
                        new_dict[dataset]['snap']['interval'] = config_dict['defaults']['snap']['interval']
                    if 'remote_server' in config_dict['defaults']['snap'].iterkeys():
                        new_dict[dataset]['snap']['remote_server'] = config_dict['defaults']['snap']['remote_server']
            ###########################################################################
            ###########################################################################
            
            ############ determine any declared overwrite conf values #################
            ###########################################################################
            if config_dict[dataset]:
                if 'user' in config_dict[dataset].iterkeys():
                    new_dict[dataset]['user'] = config_dict[dataset]['user']
                
                if 'quota' in config_dict[dataset].iterkeys():
                    new_dict[dataset]['quota'] = config_dict[dataset]['quota']
        
                if 'refquota' in config_dict[dataset].iterkeys():
                    new_dict[dataset]['refquota'] = config_dict[dataset]['refquota']
                
                if 'reservation' in config_dict[dataset].iterkeys():
                    new_dict[dataset]['reservation'] = config_dict[dataset]['reservation']
                
                if 'refreservation' in config_dict[dataset].iterkeys():
                    new_dict[dataset]['refreservation'] = config_dict[dataset]['refreservation']
                
                if 'retention' in config_dict[dataset].iterkeys():
                    new_dict[dataset]['retention'] = config_dict[dataset]['retention']
                
                if 'secure' in config_dict[dataset].iterkeys():
                    new_dict[dataset]['secure'] = config_dict[dataset]['secure']
                
                if 'contact' in config_dict[dataset].iterkeys():
                    new_dict[dataset]['contact'] = config_dict[dataset]['contact']
                    
                if 'snap' in config_dict[dataset].iterkeys():
                    if 'interval' in config_dict[dataset]['snap'].iterkeys():
                        new_dict[dataset]['snap']['interval'] = config_dict[dataset]['snap']['interval']
                    if 'remote_server' in config_dict[dataset]['snap'].iterkeys():
                        new_dict[dataset]['snap']['remote_server'] = config_dict[dataset]['snap']['remote_server']
        
            ###########################################################################
            ###########################################################################
        
            ############ add values if defaults and conf values are null ##############
            ###########################################################################
            if not new_dict[dataset]['quota']:
                new_dict[dataset]['quota'] = 'none'
            
            if not new_dict[dataset]['refquota']:
                new_dict[dataset]['refquota'] = 'none'
            
            if not new_dict[dataset]['reservation']:
                new_dict[dataset]['reservation'] = 'none'
            
            if not new_dict[dataset]['refreservation']:
                new_dict[dataset]['refreservation'] = 'none'
            
            if not new_dict[dataset]['secure']:
                new_dict[dataset]['secure'] = 'True'
            
            if not new_dict[dataset]['contact']:
                new_dict[dataset]['contact'] = zettaknight_globs.default_contact_info
        
            ###########################################################################
            ###########################################################################
        
            ############ format checking for contact variable #########################
            ###########################################################################
            if isinstance(new_dict[dataset]['contact'], list):
                contacts = False
                for addr in new_dict[dataset]['contact']:
                    if not contacts:
                        contacts = "{0}".format(addr)
                    else:
                        contacts = "{0} {1}".format(contacts, addr)
            
                new_dict[dataset]['contact'] = contacts
            ###########################################################################
            ###########################################################################

            #print("\n\ndictionary for {0} is as follows\n{1}\n\n".format(dataset, new_dict[dataset]))
        
    #print(printcolors("\n\nfull dictionary for get_conf is as follows\n{0}".format(new_dict), "OKBLUE"))
    return new_dict
    

def zfs_maintain(dset=False):
    '''
    The zfs_maintain function reads in dataset and maintenance requirements from /opt/clemson/zfs_scripts/maintain.conf

    Accepted configuration keys are:

        - remote_server
        - retention
        - reservation
        - quota
        - user
        - contact

    '''
    
    ret = {}
    protocol = "ssh"
    
    if dset and str(dset) not in zettaknight_globs.zfs_conf.iterkeys():
        ret[dset] = {}
        ret[dset]['zfs maintain'] = {1: "{0} is not a Zettaknight controlled dataset.".format(dset)}
        #zettaknight_utils.parse_output(ret)
        return ret
    
    for dataset in zettaknight_globs.zfs_conf.iterkeys():
        if dset:
            if str(dset) != str(dataset):
                continue
                
        ret[dataset] = {}
        ret[dataset]['Cleanup'] = cleanup_snaps(dataset, zettaknight_globs.zfs_conf[dataset]['retention'])
        if zettaknight_globs.zfs_conf[dataset]['quota']:
            ret[dataset]['Quota'] = set_quota(dataset, zettaknight_globs.zfs_conf[dataset]['quota'])

        if zettaknight_globs.zfs_conf[dataset]['refquota']:
            ret[dataset]['Refquota'] = set_refquota(dataset, zettaknight_globs.zfs_conf[dataset]['refquota'])

        if zettaknight_globs.zfs_conf[dataset]['reservation']:
            ret[dataset]['Reservation'] = set_reservation(dataset, zettaknight_globs.zfs_conf[dataset]['reservation'])

        if zettaknight_globs.zfs_conf[dataset]['refreservation']:
            ret[dataset]['Refreservation'] = set_refreservation(dataset, zettaknight_globs.zfs_conf[dataset]['refreservation'])
        
        if 'snap' in zettaknight_globs.zfs_conf[dataset].iterkeys():
            ret[dataset]['snapshot'] = create_snap(dataset, "quiet")

    #print(ret)
    #parse_output(ret)
    return ret
   
def _entry_point(argv=None):
    
    argparsing()
    
    print(printcolors("zettaknight version {0}\n".format(zettaknight_globs.version), "WARNING")) # print version information
    
    py_ver = sys.version_info[:2]
    py_vers = "{0}.{1}".format(py_ver[0], py_ver[1])
    
    if not str(py_vers[0]) == zettaknight_globs.required_python_version[0]:
        try:
            raise Exception("Required Python version: {0}\nInstalled Python version: {1}".format(zettaknight_globs.required_python_version, py_vers))
        except Exception as e:
            print(printcolors(e, "FAIL"))
            sys.exit(0)

    if not os.path.isfile(zettaknight_globs.identity_file):
        try:
            print(printcolors("zettaknight id file not found, generating.", "WARNING"))
            ssh_keygen(zettaknight_globs.identity_file)
        except Exception as e:
            print(printcolors("Exception encountered: {0}".format(e), "FAIL"))
            print(printcolors("Attempting to continue", "FAIL"))
            pass
        
    ret = {}
    funcname = False

    
    if len(argv) > 1:
        if 'mail_output' in argv:
            zettaknight_globs.mail_flag = True
            zettaknight_globs.nocolor_flag = True
            argv.remove('mail_output')
            
        if 'mail_error' in argv:
            zettaknight_globs.mail_error_flag = True
            zettaknight_globs.nocolor_flag = True
            argv.remove('mail_error')
        
        if len(argv) > 1:
            funcname = argv[1]
            methods = globals().copy()
            methods.update(locals())
            func = methods.get(funcname)
            if not func:
                try:
                    raise Exception("Function {0} not implemented.".format(funcname))
                except Exception as e:
                    print(printcolors(e, "FAIL"))
                    sys.exit(0)

            params = argv[2:]
            
            #create kwargs and create args

            args = []
            kwargs = {}
    
            for arg in params:
                if "=" in arg:
                    k, v = arg.split("=", 1)
                    kwargs[k] = v
                else:
                    args.append(arg)
            
            #print to key kwargs and args being passed to what function
            #print("passing args: {0} and kwargs: {1} to function : {2}".format(args, kwargs, funcname))

            try:
                if str(funcname) == 'benchmark':
                    ret = func(**kwargs)
                else:
                    zettaknight_globs.zfs_conf = _get_conf()
                    ret = func(*args, **kwargs)
            except TypeError as e:
                print(printcolors(e, "FAIL"))
                ret = printcolors(e, "FAIL")
                sys.exit(0)
        else:
            zettaknight_globs.zfs_conf = _get_conf()
            ret = create_crond_file()
            
    else:
        zettaknight_globs.zfs_conf = _get_conf()
        ret = create_crond_file()
        
    suppress_list = ["check_group_quota", "find_versions", "recover"]
    if str(funcname) not in suppress_list:
        parse_output(ret)
        
    return ret
        
    
if __name__=="__main__":

    _entry_point(sys.argv)

