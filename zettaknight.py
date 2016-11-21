#!/usr/bin/python
# -*- coding: utf-8 -*-

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

# Import python libs

import sys
import yaml
import zettaknight_globs
import os
import shutil
import argparse
import types
import inspect
import time
import logging
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

def help(methods, *args):
    
    ignore_list = [ 'pipe_this2', 'strip_input', 'mm_post', 'printcolors', 'pipe_this', 'mail_out', 'argparsing', 'replace_string', 'query_yes_no', 'parse_output', 'create_store', 'check_quiet', 'create_kwargs_from_args', 'query_return_list', 'query_return_item', 'spawn_job', 'update_crond', 'update_cron' ]
    command_list = []
    cmd_out = "Zettaknight includes the following callable methods.  To get information about a specific command,run \nzettaknight help <command>\n\n"
    for name in methods.keys():
        if isinstance(methods[name], types.FunctionType):
            if name not in ignore_list:
                command_list.append(name)
    
    ret = {}
    ret['Zettaknight'] = {}
    if len(args) > 1:
        if str(args[1]) in command_list:
            cmd_out = "{0}Displaying help for subcommand: {1}".format(cmd_out, str(args[1]))
            func = methods.get(args[1])
            func_help_out = func()
            cmd_out = "{0}\n\t{1}".format(cmd_out, func_help_out)
            
            
    else:    
        cmd_out = "{0}Command List:".format(cmd_out)
        for command in command_list:
            if not command.startswith("_"):
                cmd_out = "{0}\n\t{1}".format(cmd_out, command)
    
    ret['Zettaknight']['Help'] = {'0': cmd_out}
    
    return ret

def do_prep_work():
    '''
    this function is designed to do manage all things needed before zettaknight can run 
    '''
    ret = {}
    
    if zettaknight_globs.help_flag:
        ret = """Do Prep Work:

    Function is designed to do manage all things needed before zettaknight can run.  This includes verifying defined zpools and datasets are created,
    and maintenance jobs are scheduled.

    If Zettaknight is run without a subcommand, the Do Prep Work function is called.
    
    This function takes no arguments.  
    """

        return ret
            
    ret[zettaknight_globs.fqdn] = {}
    
    try:
    
        zettaknight_utils.zlog("[do_prep_work] starting build_out_config", "DEBUG")
        out0 = build_out_config()
        
        zlog("[do_prep_work] starting create_crond_file", "DEBUG")
        out1 = create_crond_file()
        
        zlog("[do_prep_work] starting backup_luks_headers", "DEBUG")
        out2 = backup_luks_headers()
        
        zlog("[do_prep_work] starting backup_files", "DEBUG")
        out3 = backup_files()
        
        
        ret[zettaknight_globs.fqdn]['Build Out Config'] = out0[zettaknight_globs.fqdn]['Build Config']
        ret[zettaknight_globs.fqdn][zettaknight_globs.crond_zettaknight] = out1[zettaknight_globs.fqdn][zettaknight_globs.crond_zettaknight]
        ret[zettaknight_globs.fqdn][zettaknight_globs.crond_primary] = out1[zettaknight_globs.fqdn][zettaknight_globs.crond_primary]
        ret[zettaknight_globs.fqdn][zettaknight_globs.crond_secondary] = out1[zettaknight_globs.fqdn][zettaknight_globs.crond_secondary]
        ret[zettaknight_globs.fqdn]['Backup Luks Headers'] = out2[zettaknight_globs.fqdn]['Backup Luks Headers']
        ret[zettaknight_globs.fqdn][zettaknight_globs.zettaknight_store] = out3[zettaknight_globs.fqdn][zettaknight_globs.zettaknight_store]
        
        
    except Exception as e:
        ret[zettaknight_globs.fqdn]['prep work'] = {}
        ret[zettaknight_globs.fqdn]['prep work']['1'] = {}
        zlog("{0}".format(e), "ERROR")
        ret = e  
    
    zlog("ret for [do_prep_work]:\n\t{0}".format(ret), "DEBUG")
    return ret

    
def _get_conf():
    '''
    '''   
     
    config_dict = {}
    
    zettaknight_utils.zlog("attempting to build _get_conf","DEBUG")
        
        
    ###########################################################################################
    #test if zettaknight conf file exists, if not copy default conf file out of share and exit#
    ###########################################################################################
    try:
    
        if not os.path.isfile(zettaknight_globs.config_file_new) or not os.path.isfile(zettaknight_globs.pool_config_file):
            if os.path.isfile(zettaknight_globs.default_config_file):
                if not os.path.isfile(zettaknight_globs.config_file_new):
                    shutil.copy(zettaknight_globs.default_config_file, zettaknight_globs.config_file_new)
                    print(printcolors("copied {0} to {1}".format(zettaknight_globs.default_config_file, zettaknight_globs.config_file_new), "OKBLUE"))
            else:
                raise IOError('default configuration file does not exist in {0}, cannot continue'.format(zettaknight_globs.default_config_file))
                
            if os.path.isfile(zettaknight_globs.default_pool_config_file):
                    if not os.path.isfile(zettaknight_globs.pool_config_file):
                        shutil.copy(zettaknight_globs.default_pool_config_file, zettaknight_globs.pool_config_file)
                        print(printcolors("copied {0} to {1}".format(zettaknight_globs.default_pool_config_file, zettaknight_globs.pool_config_file), "OKBLUE"))
            else:
                raise IOError('default pool configuration file does not exist in {0}, cannot continue'.format(zettaknight_globs.default_pool_config_file))
                
            zlog("default conf files have been created. Edit values then run zettaknight again to deploy the configuration", "WARNING")
            sys.exit(0)
            
        conff = open(zettaknight_globs.config_file_new, 'r')   
        config_dict = yaml.safe_load(conff)
        #test if config file is empty
        if not config_dict:
            raise ValueError('config file {0} is empty, cannot continue'.format(zettaknight_globs.config_file_new))
    except Exception as e:
        zlog("{0}".format(e), "CRITICAL")
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
            new_dict[dataset]['snap']['dgr'] = {}
            new_dict[dataset]['snap']['backup_server'] = {}
            new_dict[dataset]['snap']['translate'] = {}
            new_dict[dataset]['snap']['timeout'] = {}
            new_dict[dataset]['priority'] = {}
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
                    if 'dgr' in config_dict['defaults']['snap'].iterkeys():
                        new_dict[dataset]['snap']['dgr'] = config_dict['defaults']['snap']['dgr']
                    if 'backup_server' in config_dict['defaults']['snap'].iterkeys():
                        new_dict[dataset]['snap']['backup_server'] = config_dict['defaults']['snap']['backup_server']
                    if 'translate' in config_dict['defaults']['snap'].iterkeys():
                        new_dict[dataset]['snap']['translate'] = config_dict['defaults']['snap']['translate']
                    if 'timeout' in config_dict['defaults']['snap'].iterkeys():
                        new_dict[dataset]['snap']['timeout'] = config_dict['defaults']['snap']['timeout']
                        
                if 'priority' in config_dict['defaults'].iterkeys():
                    new_dict[dataset]['priority'] = config_dict['defaults']['priority']
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
                    if 'dgr' in config_dict[dataset]['snap'].iterkeys():
                        new_dict[dataset]['snap']['dgr'] = config_dict[dataset]['snap']['dgr']
                    if 'backup_server' in config_dict[dataset]['snap'].iterkeys():
                        new_dict[dataset]['snap']['backup_server'] = config_dict[dataset]['snap']['backup_server']
                    if 'translate' in config_dict[dataset]['snap'].iterkeys():
                        new_dict[dataset]['snap']['translate'] = config_dict[dataset]['snap']['translate']
                    if 'timeout' in config_dict[dataset]['snap'].iterkeys():
                        new_dict[dataset]['snap']['timeout'] = config_dict[dataset]['snap']['timeout'] 
                        
                if 'priority' in config_dict[dataset].iterkeys():
                    new_dict[dataset]['priority'] = config_dict[dataset]['priority']
        
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
    zlog("dictionary returned from _get_conf:\n\t{0}".format(new_dict),"DEBUG")
    return new_dict
    
def _get_pool_conf():
    
    pool_dict = {}
    zettaknight_store = ""
    contact = "" #make the last contact entry the default for all pools

    try:
        conff = open(zettaknight_globs.pool_config_file, 'r')   
        config_dict = yaml.safe_load(conff)
    except IOError as e:
        zlog("{0}".format(e), "ERROR")
        return
    
    if config_dict:
    
        for zpool in config_dict.iterkeys():
            if 'zettaknight_store' in config_dict[zpool].iterkeys():
                zettaknight_store = "{0}/zettaknight/{1}".format(zpool, zettaknight_globs.fqdn)
        
        for zpool in config_dict.iterkeys():
            pool_dict[zpool] = {}
        
            pool_dict[zpool]['ashift'] = {}
            pool_dict[zpool]['disk_list'] = {}
            pool_dict[zpool]['raid'] = {}
            pool_dict[zpool]['slog'] = {}
            pool_dict[zpool]['luks'] = {}
            pool_dict[zpool]['recordsize'] = {}
            
            if config_dict[zpool]:
                if 'ashift' in config_dict[zpool].iterkeys():
                    pool_dict[zpool]['ashift'] = config_dict[zpool]['ashift']
                    
                if 'disk_list' in config_dict[zpool].iterkeys():
                    pool_dict[zpool]['disk_list'] = config_dict[zpool]['disk_list']
                
                if 'raid' in config_dict[zpool].iterkeys():
                    pool_dict[zpool]['raid'] = config_dict[zpool]['raid']
                    
                if 'slog' in config_dict[zpool].iterkeys():
                    pool_dict[zpool]['slog'] = config_dict[zpool]['slog']
                
                if 'luks' in config_dict[zpool].iterkeys():
                    pool_dict[zpool]['luks'] = zettaknight_utils._str_to_bool(config_dict[zpool]['luks'])
                
                if 'recordsize' in config_dict[zpool].iterkeys():
                    pool_dict[zpool]['recordsize'] = config_dict[zpool]['recordsize']
                    
                if 'quota' in config_dict[zpool].iterkeys():
                    pool_dict[zpool]['quota'] = config_dict[zpool]['quota']
                
            
                if 'contact' in config_dict[zpool].iterkeys():
                    contact = config_dict[zpool]['contact']
                
                #make sure each pool has it's own zettaknight_store
                if not zettaknight_store:
                    zettaknight_store = "{0}/zettaknight/{1}".format(zpool, zettaknight_globs.fqdn)
                
        zettaknight_globs.zettaknight_store = zettaknight_store
        zlog("zettaknight_store global set to: {0}".format(zettaknight_globs.zettaknight_store),"DEBUG")
        zettaknight_globs.default_contact_info = contact
        zlog("zpool contact global set to: {0}".format(zettaknight_globs.default_contact_info),"DEBUG")
        
        if not contact:
            zlog("contact information must be defined in zpool conf, please edit and try again","CRITICAL")
            sys.exit(1)
                
        #print(printcolors(pool_dict, "OKBLUE"))                    
        zlog("dictionary returned from _get_pool_conf:\n\t{0}".format(pool_dict),"DEBUG")
        return pool_dict
        
def _get_zettaknight_conf():

    zettaknight_conf = {}
    
    try:
    
        if not os.path.isdir(zettaknight_globs.conf_dir_new): #if new directory does not exists, make it
                    os.mkdir(zettaknight_globs.conf_dir_new)
                    zettaknight_utils.zlog("created {0}".format(zettaknight_globs.conf_dir_new),"INFO")
    
        if not os.path.isfile(zettaknight_globs.zettaknight_config_file):
        
            if os.path.isfile(zettaknight_globs.default_zettaknight_config_file):
            
                shutil.copy(zettaknight_globs.default_zettaknight_config_file, zettaknight_globs.zettaknight_config_file)
                print(printcolors("copied {0} to {1}".format(zettaknight_globs.default_pool_config_file, zettaknight_globs.pool_config_file), "OKBLUE"))
                
            else:
            
                zlog("default zettaknight config file {0} does not exist".format(zettaknight_globs.default_zettaknight_config_file), "CRITICAL")
                sys.exit(1)
        
        conff = open(zettaknight_globs.zettaknight_config_file, 'r')
        config_dict = yaml.safe_load(conff)
            
        if 'zpool_max_usage' in config_dict.iterkeys():
            zettaknight_conf['zpool_max_usage'] = config_dict['zpool_max_usage']
            
        if 'parallel' in config_dict.iterkeys():
            zettaknight_conf['parallel'] = config_dict['parallel']
            
        if 'config_enforcement' in config_dict.iterkeys():
            zettaknight_conf['config_enforcement'] = zettaknight_utils._str_to_bool(config_dict['config_enforcement'])
            
        if 'zpool_config_enforcement' in config_dict.iterkeys():
            zettaknight_conf['zpool_config_enforcement'] = zettaknight_utils._str_to_bool(config_dict['zpool_config_enforcement'])
            
        if 'level_zlog' in config_dict.iterkeys():
            zettaknight_conf['level_zlog'] = config_dict['level_zlog']
            
        if 'sync_timeout' in config_dict.iterkeys():
            zettaknight_conf['sync_timeout'] = config_dict['sync_timeout']
            
            
        #exit if required values are empty
        
        required = ['config_enforcement', 'zpool_config_enforcement', 'parallel']
        if not all (req in zettaknight_conf.iterkeys() for req in required):
        
            zlog("{0} are all required\n\trefer to {1}\n\t\tzettaknight_conf: {2}".format(required, zettaknight_globs.default_zettaknight_config_file, zettaknight_conf),"CRITICAL")
            sys.exit(1)

        return zettaknight_conf
    
    except Exception as e:
        zlog("{0}".format(e), "ERROR")
        return
        
    
 
   
def _entry_point(argv=None):
    
    #argparsing()
    
    #zlog("zettaknight start", "DEBUG")
    
    print(printcolors("zettaknight version {0}\nstart: {1}".format(zettaknight_globs.version, datetime.datetime.today()), "WARNING")) # print version information
    start_time = time.time()
        
    py_ver = sys.version_info[:2]
    py_vers = "{0}.{1}".format(py_ver[0], py_ver[1])
    
    if not str(py_vers[0]) == zettaknight_globs.required_python_version[0]:
        try:
            raise Exception("Required Python version: {0}\nInstalled Python version: {1}".format(zettaknight_globs.required_python_version, py_vers))
        except Exception as e:
            zlog("{0}".format(e), "CRITICAL")
            sys.exit(1)

    #############################################################################
    #test to determine if pool and child objects are both defined in config_file#
    #############################################################################
    
    #############################################################################
    #############################################################################
    #############################################################################

    if not os.path.isfile(zettaknight_globs.identity_file):
        try:
            print(printcolors("zettaknight id file not found, generating.", "WARNING"))
            ssh_keygen(zettaknight_globs.identity_file)
        except Exception as e:
            print(printcolors("Exception encountered: {0}".format(e), "FAIL"))
            print(printcolors("Attempting to continue", "FAIL"))
            pass
        
    ret = {}
    args = []
    kwargs = {}
    
    funcname = False

    methods = globals().copy()
    methods.update(locals())
    
    if len(argv) > 1:
            
        if 'help' in argv:
            zettaknight_globs.help_flag = True
            funcname = "help"
            func = methods.get(funcname)
            argv.remove('help')
            ret = func(methods, *argv)
            parse_output(ret)
            return ret
            
        if 'mail_output' in argv:
            zettaknight_globs.mail_flag = True
            zettaknight_globs.nocolor_flag = True
            argv.remove('mail_output')
            
        if 'mail_error' in argv:
            zettaknight_globs.mail_error_flag = True
            zettaknight_globs.nocolor_flag = True
            argv.remove('mail_error')
        
        if len(argv) > 1:
            if "level" in argv[1]:
                func = methods.get("do_prep_work")
                #kwargs = {}
                k, v = argv[1].split("=", 1)
                kwargs[k] = v
            else:
                funcname = argv[1]
                func = methods.get(funcname)

            if not func:
                try:
                    raise Exception("Function {0} not implemented.".format(funcname))
                except Exception as e:
                    zlog("{0}".format(e), "ERROR")
                    sys.exit(0)

            params = argv[2:]


            for arg in params:
                if "=" in arg:
                    k, v = arg.split("=", 1)
                    kwargs[k] = v
                else:
                    args.append(arg)

            if 'level' in kwargs.iterkeys():
                zettaknight_globs.level_zlog = kwargs["level"]
                kwargs.pop('level')

            
            #print to key kwargs and args being passed to what function
            #print("passing args: {0} and kwargs: {1} to function : {2}".format(args, kwargs, funcname))

            try:
                if str(funcname) == 'benchmark':
                    ret = func(**kwargs)
                else:
                    zettaknight_globs.zettaknight_conf = _get_zettaknight_conf()
                    zlog("dictionary returned from _get_zettaknight_conf:\n\t{0}".format(zettaknight_globs.zettaknight_conf),"DEBUG")
                    
                    zettaknight_globs.zfs_conf = _get_conf()
                    zettaknight_globs.zpool_conf = _get_pool_conf()
                    ret = func(*args, **kwargs)
            except TypeError as e:
                zlog("{0}".format(e), "ERROR")
                sys.exit(0)
        else:
            zettaknight_globs.zettaknight_conf = _get_zettaknight_conf()
            zlog("dictionary returned from _get_zettaknight_conf:\n\t{0}".format(zettaknight_globs.zettaknight_conf),"DEBUG")
            
            zettaknight_globs.zfs_conf = _get_conf()
            zettaknight_globs.zpool_conf = _get_pool_conf()
            ret = do_prep_work()
            
    else:
        zettaknight_globs.zettaknight_conf = _get_zettaknight_conf()
        zlog("dictionary returned from _get_zettaknight_conf:\n\t{0}".format(zettaknight_globs.zettaknight_conf),"DEBUG")
        
        zettaknight_globs.zfs_conf = _get_conf()
        zettaknight_globs.zpool_conf = _get_pool_conf()
        ret = do_prep_work()
        
    suppress_list = ["check_group_quota", "find_versions", "recover"]
    
    zettaknight_globs.elapsed_time = time.time() - start_time
        
    if str(funcname) not in suppress_list:
        parse_output(ret)

    print(printcolors("elapsed time: {0} seconds".format(zettaknight_globs.elapsed_time), "WARNING"))    
    return ret
        
    
if __name__=="__main__":

    _entry_point(sys.argv)

