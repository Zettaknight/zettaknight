#!/usr/bin/python
# -*- coding: utf-8 -*-
# Import python libs

import sys
import yaml
import zettaknight_globs
from zettaknight_zpool import *
from zettaknight_utils import *
from zettaknight_zfs import *
from zettaknight_recover import *

        
def help (kwargs=None):
    print ("Need to add a help function")

    
def _get_conf():
    '''
    '''
    config_dict = {}
    if os.path.isfile(zettaknight_globs.config_file):
        try:
            conff = open(zettaknight_globs.config_file, 'r')
            config_dict = yaml.safe_load(conff)
        
        except Exception as e:
            print(printcolors("Configuration file not found.", "FAIL"))
            print(printcolors(e, "FAIL"))
            sys.exit(0)

        for dataset in config_dict.iterkeys():
        
            if 'user' not in config_dict[dataset].iterkeys():
                config_dict[dataset]['user'] = 'root'
        
            if 'reservation' not in config_dict[dataset].iterkeys():
                config_dict[dataset]['reservation'] = 'none'
        
            if 'quota' not in config_dict[dataset].iterkeys():
                config_dict[dataset]['quota'] = 'none'
            
            if 'secure' not in config_dict[dataset].iterkeys():
                config_dict[dataset]['secure'] = True
        
            if 'contact' not in config_dict[dataset].iterkeys():
                #config_dict[dataset]['contact'] = 'COREINFRASERVICES_MONITOR@lists.clemson.edu'
                config_dict[dataset]['contact'] = zettaknight_globs.default_contact_info
            
            if isinstance(config_dict[dataset]['contact'], list):
                contacts = False
                for addr in config_dict[dataset]['contact']:
                    if not contacts:
                        contacts = "{0}".format(addr)
                    else:
                        contacts = "{0} {1}".format(contacts, addr)
            
                config_dict[dataset]['contact'] = contacts

    
    return config_dict
    

def zfs_maintain():
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
    
    
    for dataset in zettaknight_globs.zfs_conf.iterkeys():
        ret[dataset] = {}
        ret[dataset]['Cleanup'] = cleanup_snaps(dataset, zettaknight_globs.zfs_conf[dataset]['retention'])
        if zettaknight_globs.zfs_conf[dataset]['quota']:
            ret[dataset]['Quota'] = set_quota(dataset, zettaknight_globs.zfs_conf[dataset]['quota'])
            for exit_status, output in ret[dataset]['Quota'].iteritems():
                if str(exit_status) == "0" and str(output) == "Job succeeded":
                    ret[dataset]['Quota'][exit_status] = "Quota set to: {0}".format(zettaknight_globs.zfs_conf[dataset]['quota'])

        if zettaknight_globs.zfs_conf[dataset]['reservation']:
            ret[dataset]['Reservation'] = set_reservation(dataset, zettaknight_globs.zfs_conf[dataset]['reservation'])
            for exit_status, output in ret[dataset]['Reservation'].iteritems():
                if str(exit_status) == "0" and str(output) == "Job succeeded":
                    ret[dataset]['Reservation'][exit_status] = "Reservation set to: {0}".format(zettaknight_globs.zfs_conf[dataset]['reservation'])
        
        if 'snap' in zettaknight_globs.zfs_conf[dataset].iterkeys():
            if not zettaknight_globs.zfs_conf[dataset]['snap']:
                ret[dataset]['Snapshot'] = create_snap(dataset, "quiet")

            if zettaknight_globs.zfs_conf[dataset]['snap']:
                if 'remote_server' in zettaknight_globs.zfs_conf[dataset]['snap'].iterkeys():
                    for remote_server in zettaknight_globs.zfs_conf[dataset]['snap']['remote_server']:
                        if str(zettaknight_globs.zfs_conf[dataset]['secure']) == "False":
                            protocol = "xinetd"
                        
                        try:    
                            if str(zettaknight_globs.zfs_conf[dataset]['primary']) == str(zettaknight_globs.fqdn):
                                nosnap = False
                            else:
                                nosnap = True
                        except KeyError:
                            nosnap = False
                            pass

                        ret[dataset]['snapshot to {0}'.format(remote_server)] = take_snap(dataset, zettaknight_globs.zfs_conf[dataset]['user'], remote_server, zettaknight_globs.zfs_conf[dataset]['secure'], nosnap)
                        
            if 'interval' in zettaknight_globs.zfs_conf[dataset]['snap'].iterkeys():
                arg_list = []
                cron_line = "{0}/zettaknight.py mail_error &> /dev/null".format(zettaknight_globs.base_dir)
                #arg_list.append(cron_line)
                for cron_item in zettaknight_globs.zfs_conf[dataset]['snap']['interval']:
                    for k, v in cron_item.iteritems():
                        cron_string = "{0}={1}".format(k, v)
                        arg_list.append(cron_string)
                #print("arg_list : {0}".format(arg_list))
                a, b = ' '.join(arg_list).split(" ")
                ret[dataset]['Update Cron'] = zettaknight_utils.update_cron(cron_line, a, b)
                
    #make sure svn is updating each night
    #add entry for zfs_monitor.sh and cron entry
    cron_monitor = "{0}/zettaknight.py zfs_monitor \"{1}\" &> /dev/null".format(zettaknight_globs.base_dir, zettaknight_globs.zfs_conf[dataset]['contact'])
    
    ret[dataset]['zfs_monitor'] = zettaknight_utils.update_cron(cron_monitor, everyminute=15)

    #print(ret)
    parse_output(ret)
    
    return ret
   
def _entry_point(argv=None):
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
    
    zettaknight_globs.zfs_conf = _get_conf()
    #print("ZETTAKNIGHT ARGS: {0}".format(argv))
    #print("ZETTAKNIGHT ARGS_LEN: {0}".format(len(argv)))
    
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
            #print(params)
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
                ret = func(*args, **kwargs)
            except TypeError as e:
                print(printcolors(e, "FAIL"))
                ret = printcolors(e, "FAIL")
                sys.exit(0)
        else:
            ret = zfs_maintain()
            
    else:
        ret = zfs_maintain()
        
    return ret
        
    
if __name__=="__main__":

    _entry_point(sys.argv)
