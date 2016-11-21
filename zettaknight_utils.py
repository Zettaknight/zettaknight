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
import logging
import logging.handlers
import subprocess
import shlex
import yaml
import json
import os
import socket
import inspect
import datetime
import re
import termios
import shutil
import paramiko

 
import zettaknight_globs
import zettaknight_zfs
 

def zlog(*args):
    '''
    log function used for zettaknight purposes
    '''
    
    if len(args) != 2:
        ret[zettaknight_globs.fqdn]['log']['1'] = "log function takes exactly 2 arguments (message, level)"
        parse_output(ret)
        return

    message = args[0]
    level = args[1]
    
    ret = ""
    
    date = datetime.datetime.today()
        
    #test if level_zlog in globs is a string or int
    if zettaknight_globs.zettaknight_conf is not None:
    
        if 'level_zlog' not in zettaknight_globs.zettaknight_conf.iterkeys():
        
            level_int = 4
    
        else:

            if not isinstance(zettaknight_globs.zettaknight_conf['level_zlog'], int):
        
                if zettaknight_globs.zettaknight_conf['level_zlog'] == "DEBUG":
                    level_int = 5
                if zettaknight_globs.zettaknight_conf['level_zlog'] == "INFO":
                    level_int = 4
                if zettaknight_globs.zettaknight_conf['level_zlog'] == "WARNING":
                    level_int = 3
                if zettaknight_globs.zettaknight_conf['level_zlog'] == "ERROR":
                    level_int = 2
                if zettaknight_globs.zettaknight_conf['level_zlog'] == "CRITICAL":
                    level_int = 1
                    
    else: #if zettaknight_conf is empty, allows ERROR and CRITICAL messages to be reported to standard out
    
        level_int = 4
    
    if level_int >= 5:
    
        if level.upper() == "DEBUG":
            level = printcolors("{0}".format(level.upper()), "OKBLUE")
            ret = "{0} {1} {2}".format(date, level, message)
    
    if level_int >= 4:
    
        if level.upper() == "INFO":
            level = printcolors("{0}".format(level.upper()), "OKBLUE")
            ret = "{0} {1} {2}".format(date, level, message)
            
        if level.upper() == "SUCCESS":
            level = printcolors("{0}".format(level.upper()), "OKGREEN")
            ret = "{0} {1} {2}".format(date, level, message)
        
    if level_int >= 3:
        if level.upper() == "WARNING":
            level = printcolors("{0}".format(level.upper()), "WARNING")
            ret = "{0} {1} {2}".format(date, level, message)
        
    if level_int >= 2:
        if level.upper() == "ERROR":
            level = printcolors("{0}".format(level.upper()), "FAIL")
            ret = "{0} {1} {2}".format(date, level, message)
        
    if level_int >= 1:
        if level.upper() == "CRITICAL":
            level = printcolors("{0}".format(level.upper()), "HEADER")
            ret = "{0} {1} {2}".format(date, level, message)

    
    if ret:
        print ret
    
    return ret

        
def pipe_this(*args):
 
    '''
    This function interates over each element in the list and passes it through a pipe.
 
    Example:
    ls /tmp | grep "bob" | grep "20150910"
    would be
    pipe_this("ls /tmp", "grep bob", "grep 20150910")
 
    The function returns the subprocess object of the piped commands.
    '''
    cmd_list = args
    pipe = None
    for cmd in cmd_list:
        if pipe is None:
            pipe = subprocess.Popen(shlex.split(cmd), stdout = subprocess.PIPE)
 
        else:
            pipe = subprocess.Popen(shlex.split(cmd), stdin = pipe.stdout, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
 
    pipe.wait()
    ret = pipe
 
    return ret
    
def pipe_this2(arg):
 
    '''
    This function is a re-write of the orginal pipe_this. pipe_this2 better replicates the standard pipe notation familiar in bash.
 
    Example:
    ls /tmp | grep "bob" | grep "20150910"
    would be
    pipe_this2("ls /tmp | grep bob | grep 20150910")
    '''
 
    #print(arg)
    try:
        if "|" in arg:
            cmd_list = arg.split("|")
            #print(cmd_list)
        else:
            raise Exception("| not found in command, exiting")
    except Exception as e:
            zettaknight_utils.zlog("funtion pipe_this2 encountered an unrecoverable error: {0}".format(e), "CRITICAL")
            sys.exit(1)
 
    pipe = None
    for cmd in cmd_list:
        #cmd = cmd.split()
        if pipe is None:
            pipe = subprocess.Popen(shlex.split(cmd), stdout = subprocess.PIPE)
 
        else:
            pipe = subprocess.Popen(shlex.split(cmd), stdin = pipe.stdout, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
 
    pipe.wait()
    ret = pipe
 
    return ret
 
 
 
def mail_out(email_message, email_subject, email_recipient):
    '''
    multiple email recipients can be denoted as "<email 1> <email 2>"
    '''
    
    ret = {}
    ret[zettaknight_globs.fqdn] = {}
    ret[zettaknight_globs.fqdn]['mail'] = {}     
 
    mail_out_cmd = "bash {0} -s '{2}' -r '{3}' -m '{1}'".format(zettaknight_globs.mail_out_script, email_message, email_subject, email_recipient)
    ret[zettaknight_globs.fqdn]['mail'] = spawn_job(mail_out_cmd)
 
    return ret
    
 
def parse_output(out_dict):

    zlog("parse_output started, dict obj passed:\n\t{0}".format(out_dict), "DEBUG")
    
    '''
    accepts information in the following format 
    ret[dataset]['job'][<ret code>][<payload>]
    '''
    
    Zlogger = logging.getLogger('Zlogger')
    Zlogger.setLevel(logging.INFO)

    handler = logging.handlers.SysLogHandler(address = '/dev/log')
    Zlogger.addHandler(handler)

#    if zettaknight_globs.mm_flag:
#        zettaknight_globs.nocolor_flag = True

    for dataset in out_dict.iterkeys():
        json_out = {}
        json_out["dataset"] = dataset
        json_out["elapsed time (sec)"] = zettaknight_globs.elapsed_time
        for job in out_dict[dataset].iterkeys():
            json_out["job"] = job
            for exit_status, output in out_dict[dataset][job].iteritems():
                if isinstance(output, dict):
                    for value in out_dict[dataset][job][exit_status].itervalues():
                        for exit_status, output in value.iteritems():
                           json_out["exit status"] = exit_status
                           json_out["output"] = output

                else:
                    json_out["exit status"] = exit_status
                    json_out["output"] = output

            Zlogger.info(json.dumps({"Zettaknight": json_out}, sort_keys = True))

    #print(printcolors("dictionary object passed to parse_output:\n{0}".format(out_dict), "WARNING"))
    for dataset in out_dict.iterkeys():
        global_ret = ""
        mail_this = False
        a = printcolors("\nDataset: {0}\n────────┐".format(dataset), "HEADER")
        print(a)
        for job in out_dict[dataset].iterkeys():
            #print(printcolors("    {0}:".format(job), "OKBLUE"))
            for exit_status, output in out_dict[dataset][job].iteritems():
                if isinstance(output, dict):
                    for value in out_dict[dataset][job][exit_status].itervalues():
                        for exit_status, output in value.iteritems():
                            #print("\n\noutput is : \n{0}\n\n ".format(output))
                            output = str(output.replace('\n', '\n               '))
                else:
                    output = str(output.replace('\n', '\n               '))
    
                if str(exit_status) is "0":
                    task = "{0}".format(printcolors("    ├────────┬ {0}:".format(job),"OKBLUE"))
                    task_output = "{0}".format(printcolors("         ├──────── {0}\n".format(output), "OKGREEN"))
                else:
                    if zettaknight_globs.mail_error_flag:
                        mail_this = True
                        
                    task = "{0}".format(printcolors("    ├────────┬ {0}:".format(job), "OKBLUE"))
                    task_output = "{0}".format(printcolors("         ├──────── {0}\n".format(output), "FAIL"))
                    
                msg = "{0}\n{1}".format(task, task_output)
                
            global_ret = "{0}{1}\n".format(global_ret, msg)
            
        print(global_ret)
 #       if zettaknight_globs.mm_flag:
 #           mm_msg = re.sub("[├─┬┐]", "", global_ret)
 #           mm_msg = re.sub("%", " percent", mm_msg)
 #           mm_msg = re.sub("    ", "", mm_msg)
 #           mm_post(mm_msg)
        
        if zettaknight_globs.mail_flag or mail_this:
            global_ret = "Zettaknight:\n{0}{1}".format(a, global_ret)
            try:
                contact = zettaknight_globs.zfs_conf[dataset]['contact']
            except KeyError:
                contact = zettaknight_globs.default_contact_info

            mail_sub = re.sub("[├─┬┐]", "", a)
            mail_msg = re.sub("[├─┬┐]", "", global_ret) #re.sub = regular expression substitution (sed)

            send_mail = mail_out(mail_msg, "Job report for Dataset: {0}, on {1}".format(dataset, zettaknight_globs.fqdn), contact)
 
    return global_ret

def printcolors(msg, value):
    #printcolors uses ansi color codes to change output colors
 
    colors = {
        'HEADER' : '\033[95m',
        'OKBLUE' : '\033[96m',
        'OKGREEN' : '\033[92m',
        'WARNING' : '\033[93m',
        'FAIL' : '\033[91m',
        'ENDC' : '\033[0m'
    }
 
    if zettaknight_globs.nocolor_flag:
        return(str(msg))
 
    else:
        return(colors[value] + str(msg) + colors['ENDC'])
 
 
def spawn_job(cmd):
 
    #print(_printcolors("\033[0mnRunning command: {0}".format(cmd), "HEADER"))
    ret = {}
    try:
        zlog("[spawn_job] running command:\n\t{0}".format(cmd), "DEBUG")
        cmd_run = subprocess.Popen(shlex.split(cmd), stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
        cmd_run.wait()
        cmd_run_stdout = cmd_run.stdout.read()
        if not cmd_run_stdout:
            if int(cmd_run.returncode) == 0:
                cmd_run_stdout = "Job succeeded"
            else:
                cmd_run_stdout = "Job failed"
        ret = {cmd_run.returncode: cmd_run_stdout}
 
    except Exception as e:
        returncode = 1
        ret = {returncode: e}
        print(printcolors(ret, "FAIL"))
        pass
        
    zlog("[spawn_job] return:\n\t{0}".format(ret), "DEBUG")
    return ret
    
def spawn_jobs(*args):

    '''
    function expects a list
    '''
    
    zlog("args of type {0} passed to spawn_jobs:\n\t{1}".format(type(args), args), "DEBUG")

    output = {}
    ret = []
    
    try:
        for arg in args:
            if isinstance(arg, list):
                for list_item in arg:
                    zlog("starting background job:\n\t{0}".format(list_item), "INFO")
                    output["{0}".format(list_item)] = subprocess.Popen(shlex.split(list_item), stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
            else:
                zlog("spawn_jobs expected a list, instead recieved a {0}".format(type(arg)), "CRITICAL")
        
        for out in output.itervalues():
            zlog("issuing wait to object:\n\t{0}".format(out), "INFO")
            out.wait()
            stdout = out.stdout.read()
            if not stdout:
                if int(out.returncode) == 0:
                    stdout = "Job succeeded"
                else:
                    stdout = "Job failed"
            	
            ret.append({out.returncode: stdout})
            
    except Exception as e:
        returncode = 1
        ret.append({returncode: e})
        zlog("{0}".format(e), "ERROR")
        pass
        
    return ret

 
def ssh_keygen(keyfile, remote_ssh=False):
    '''
    '''
    
    import paramiko
    
    ret = {}
    
    if zettaknight_globs.help_flag:
        ret = """SSH Keygen:

    Function to create a ssh key - either the default Zettaknight key defined in Zettaknight conf files, or a keyfile passed in as an argument.
    
    Usage:
        zettaknight ssh_keygen
    
    Optional Arguments:
        keyfile
            Specifies a location for the new keyfile.  By default this information is pulled from configuration files.
        remote_ssh
            Specifies a remote host to copy the ssh key to.
            
    Normally this function is called by other Zettaknight functions and does not need to be called directly."""

        return ret
        
    ret[zettaknight_globs.fqdn] = {}
    ret[zettaknight_globs.fqdn]['Generate SSH Key'] = {}
        
    if not keyfile:
        keyfile=zettaknight_globs.identity_file
    
    ssh_cmd = "bash {0} -k {1}".format(zettaknight_globs.ssh_keygen_script, keyfile)
    if remote_ssh:
        ssh_cmd = "{0} -r {1}".format(ssh_cmd, remote_ssh)
        try:
            user, remote = remote_ssh.split("@")
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(remote, username=user, key_filename=keyfile)
            remote_sudo_cmd = "hostname"
            ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(remote_sudo_cmd)
            ssh_output = ssh_stdout.readlines()
            print(ssh_output)
            if ssh_output:
                ret[zettaknight_globs.fqdn]['Generate SSH Key'] = {'0': "Nothing to do.\nKey authentication already setup for {0} with keyfile {1}".format(remote_ssh, keyfile)}
                #parse_output(ret)
                #return ret
        except Exception as e:
            pass
    
    try:
        ret[zettaknight_globs.fqdn]['Generate SSH Key'] = spawn_job(ssh_cmd)
    except Exception as e:
        ret[zettaknight_globs.fqdn]['Generate SSH Key']['1'] = {}
        ret[zettaknight_globs.fqdn]['Generate SSH Key']['1'] = e
        print(printcolors(e,"FAIL"))
        
    #arse_output(ret)
    
    return ret
 
def replace_keys(**kwargs):
    '''
    '''
    
    
    ret = {}
    
    if zettaknight_globs.help_flag:
        ret = """Replace Keys:

    Function to create a new ssh key and replace old luks keys on defined luks devices
    
    Usage:
        zettaknight replace_keys keyfile=<keyfile>
    
    Required Arguments:
        keyfile
            Specifies a name for the new keyfile.  
        
    Optional Arguments:
        delete
            If delete=True is specified, the old keyfile will be deleted after it is replaced.
            
    """

        return ret
        
    ret[zettaknight_globs.fqdn] = {}   
    ret[zettaknight_globs.fqdn]['Replace SSH Keys'] = {}
    ret[zettaknight_globs.fqdn]['Create SSH Key'] = {}
    ret[zettaknight_globs.fqdn]['Replace SSH Keys']['1'] = {}
    
    if 'keyfile' in kwargs.iterkeys():
        keyfile = kwargs['keyfile']
        if not os.path.exists(keyfile):
            ret[zettaknight_globs.fqdn]['Create SSH Key'] = ssh_keygen(keyfile)
    else:
        ret[zettaknight_globs.fqdn]['Replace SSH Keys']['1'] = "keyfile is empty, replace_keys requires a keyfile"
        return ret
    
    
    try:
        luks_key_cmd = "bash {0} -k {1}".format(zettaknight_globs.luks_key_script, keyfile)
        if 'delete' in kwargs.iterkeys():
            luks_key_cmd = "{0} -k {1} -d".format(zettaknight_globs.luks_key_script, destination_id)
    
        ret[zettaknight_globs.fqdn]['Replace Luks Keys'] = spawn_job(luks_key_cmd)
    except Exception as e:
        zlog("{0}".format(e), "ERROR")
        ret[zettaknight_globs.fqdn]['Replace SSH Keys']['1'] = e
        
    return ret
 
def backup_luks_headers(**kwargs):
    ret = {}
    if zettaknight_globs.help_flag:
        ret = """Backup LUKS Headers:

    Function to backup headers for currently defined LUKS devices.  By default, headers are backed up to the
    Zettaknight store defined in configuration files.  Target argument can be supplied to redirect where the
    headers are backed up to.
    
    Usage:
        zettaknight backup_luks_headers  (target=<output directory>)
    
    Optional Arguments:
        target
            Redirects output to provided directory.
            
    """

        return ret
        
    ret[zettaknight_globs.fqdn] = {}
    
    #set location for luks header backups if empty
    if 'target' in kwargs.iterkeys():
        target = kwargs['target']
    else:
        target = zettaknight_globs.luks_header_dir
    
    try:
        if target:
            if not os.path.isdir(target):
                os.mkdir(target)
            luks_backup_cmd = "bash {0} -l {1}".format(zettaknight_globs.luks_header_backup_script, target)
            ret[zettaknight_globs.fqdn]['Backup Luks Headers'] = spawn_job(luks_backup_cmd)
    except Exception as e:
        ret[zettaknight_globs.fqdn]['1'] = e
        pass
        
    return ret
                
    
    
def check_quiet(quiet):
    
    if quiet:
        if str(quiet) is not "quiet":
            try:
                raise Exception("{0} argument not recognized by function: {1}".format(quiet, inspect.stack()[1][3]))
            except Exception as e:
                zlog("{0}".format(e), "WARNING")
                sys.exit(0)
            
    return quiet
 

def create_config(**kwargs):
    '''
    '''
    
    ret = {}
    
    if zettaknight_globs.help_flag:
        ret = """Create Config:

    Function to create/update configuration files for newly created or previously unmanaged datasets.
    User will be queried to provide any information that is not provided as an argument or in configuration
    files.
    
    Usage:
        zettaknight create_config (dataset=<dataset> <arg>=<value>)
    
    Optional Arguments:
        dataset
            Dataset name configuration is to be created for
        user
            Username to use for snapshot replication
        quota
            Quota to set on dataset
        refquota
            Refquota to set on dataset
        reservation
            Reservation to set on dataset
        refreservation
            Refreservation to set on dataset
        retention
            Number of days to keep snapshots
        secure
            Whether snapshots should be replicated over SSH
        contact
            Contact e-mail to send job error output to.
        interval
            Interval at which to take snapshots.
        remote_server
            Remote server to replicate snapshots to."""

        return ret
        
    ret[zettaknight_globs.fqdn] = {}
    ret[zettaknight_globs.fqdn]['Create Config'] = {}
    
    #print(kwargs)
    new_conf = {}
    
    #create var dictionary and depth
    var = {}
    var['snap'] = {}
    var['snap']['interval'] = {}
    var['snap']['remote_server'] = {}
    var['reservation'] = {}
    var['refreservation'] = {}
    var['quota'] = {}
    var['refquota'] = {}
    var['secure'] = {}
    var['user'] = {} 
    var['retention'] = {}
    var['contact'] = {}
    
    
    dataset_list = []
    #config_dict = zettaknight_globs.zfs_conf
    
    conff = open(zettaknight_globs.config_file_new, 'r')   
    config_dict = yaml.safe_load(conff)
        
    #print(config_dict)
    
    #if a dataset is passed in, only do work for that particular dataset
    if 'dataset' in kwargs.iterkeys():
        #print("a dataset was passed in : {0}").format(kwargs['dataset'])
        dataset = kwargs['dataset']
        dataset_list.append(dataset)
    else:
        if config_dict:
            for dset in config_dict.iterkeys():
                if not dset in dataset_list:
                    #print("dataset {0} defined in configuration file, not in arguments. Adding to list".format(dset))
                    dataset_list.append(dset)
                        
    #print("dataset_list = {0}".format(dataset_list))
                    
    for dataset in dataset_list:
        #print(dataset)
        
        
        if 'defaults' in config_dict.iterkeys():
            if 'user' in config_dict['defaults'].iterkeys():
                var['user'] = config_dict['defaults']['user']
                
            if 'quota' in config_dict['defaults'].iterkeys():
                var['quota'] = config_dict['defaults']['quota']
                
            if 'refquota' in config_dict['defaults'].iterkeys():
                var['refquota'] = config_dict['defaults']['refquota']
                
            if 'reservation' in config_dict['defaults'].iterkeys():
                var['reservation'] = config_dict['defaults']['reservation']
                
            if 'refreservation' in config_dict['defaults'].iterkeys():
                var['refreservation'] = config_dict['defaults']['refreservation']
                
            if 'retention' in config_dict['defaults'].iterkeys():
                var['retention'] = config_dict['defaults']['retention']
                
            if 'secure' in config_dict['defaults'].iterkeys():
                var['secure'] = config_dict['defaults']['secure']
                
            if 'contact' in config_dict['defaults'].iterkeys():
                var['contact'] = config_dict['defaults']['contact']
                
            if 'snap' in config_dict['defaults'].iterkeys():
                if 'interval' in config_dict['defaults']['snap'].iterkeys():
                    var['snap']['interval'] = config_dict['defaults']['snap']['interval']
                if 'remote_server' in config_dict['defaults']['snap'].iterkeys():
                    var['snap']['remote_server'] = config_dict['defaults']['snap']['remote_server']
                
        # if kwargs are passed in, overwrite defaults
        if 'user' in kwargs.iterkeys():
            var['user'] = kwargs['user']

        if 'quota' in kwargs.iterkeys():
            var['quota'] = kwargs['quota']
            
        if 'refquota' in kwargs.iterkeys():
            var['refquota'] = kwargs['refquota']
            
        if 'reservation' in kwargs.iterkeys():
            var['reservation'] = kwargs['reservation']
            
        if 'refreservation' in kwargs.iterkeys():
            var['refreservation'] = kwargs['refreservation']
            
        if 'retention' in kwargs.iterkeys():
            var['retention'] = kwargs['retention']
            
        if 'secure' in kwargs.iterkeys():
            var['secure'] = kwargs['secure']
            
        if 'contact' in kwargs.iterkeys():
            #var['contact'] = kwargs['contact']
            var['contact'] = list(strip_input(kwargs['contact']).split(" "))

        if 'interval' in kwargs.iterkeys():
            #var['snap']['interval'] = kwargs['interval']
            var['snap']['interval'] = list(strip_input(kwargs['interval']).split(" "))
                    
        if 'remote_server' in kwargs.iterkeys():
            #var['snap']['remote_server'] = kwargs['remote_server']
            var['snap']['remote_server'] = list(strip_input(kwargs['remote_server']).split(" "))   
        
        
        
        #test if defaults and kwargs are empty, if so, prompt user for input
        if not var['user']:
            var['user'] = query_return_item("username for snapshot replication? ")
            
        if not var['quota']:
            var['quota'] = query_return_item("Enter quota for {0}: ".format(dataset))
            
        if not var['refquota']:
            var['refquota'] = 'none'
            
        if not var['reservation']:
            var['reservation'] = query_return_item("Enter reservation for {0}: ".format(dataset))
            
        if not var['refreservation']:
            var['refreservation'] = 'none'
            
        if not var['retention']:
            var['retention'] = query_return_item("How many days would you like zettaknight to keep snapshots for {0}: ".format(dataset))
            
        if not var['secure']:
            var['secure'] = query_yes_no("send snaps over ssh?: ")
        
        if not var['contact']:
            var['contact'] = query_return_list("Who do you want zettaknight to contact when an error is encountered? [person1@example.com person2@example.com ...]")
        
        if not var['snap']['interval']:
            var['snap']['interval'] = query_return_list("How often would you like zettaknight to run backups?\ni.e run every 4 hours [everyhour=4], to run at 10:30am, [hour=10]")

        if not var['snap']['remote_server']:
            var['snap']['remote_server'] = query_return_list("What server(s) do you want to replicate to? Will accept DNS names or IP addresses")
            
            
        
        #if var is defined for in defaults, and 
        if 'defaults' in config_dict.iterkeys():
            if 'user' in config_dict['defaults'].iterkeys():
                if var['user'] == config_dict['defaults']['user']:
                    del var['user']
                
            if 'quota' in config_dict['defaults'].iterkeys():
                if var['quota'] == config_dict['defaults']['quota']:
                    del var['quota']
                
            if 'refquota' in config_dict['defaults'].iterkeys():
                if var['refquota'] == config_dict['defaults']['refquota']:
                    del var['refquota']
                
            if 'reservation' in config_dict['defaults'].iterkeys():
                if var['reservation'] == config_dict['defaults']['reservation']:
                    del var['reservation']
                
            if 'refreservation' in config_dict['defaults'].iterkeys():
                if var['refreservation'] == config_dict['defaults']['refreservation']:                    
                    del var['refreservation']
                
            if 'retention' in config_dict['defaults'].iterkeys():
                if var['retention'] == config_dict['defaults']['retention']:
                    del var['retention']
                
            if 'secure' in config_dict['defaults'].iterkeys():
                if var['secure'] == config_dict['defaults']['secure']:
                    del var['secure']
                
            if 'contact' in config_dict['defaults'].iterkeys():
                if var['contact'] == config_dict['defaults']['contact']:
                    del var['contact']
                
            if 'snap' in config_dict['defaults'].iterkeys():
                if 'interval' in config_dict['defaults']['snap'].iterkeys():
                    if var['snap']['interval'] == config_dict['defaults']['snap']['interval']:
                        del var['snap']['interval']
                if 'remote_server' in config_dict['defaults']['snap'].iterkeys():
                    if var['snap']['remote_server'] == config_dict['defaults']['snap']['remote_server']:
                        del var['snap']['remote_server']
                if not var['snap']: #if var['snap'] is empty, remove it so it is not printed by the yaml.safe.dump
                    del var['snap']

        new_conf[str(dataset)] = var
        config_dict[str(dataset)] = var
                    
    print(printcolors("\n\n\nThe following will be added to {0}\n", "HEADER").format(zettaknight_globs.config_file_new))
    out = yaml.safe_dump(new_conf, default_flow_style=False)
    out2 = yaml.safe_dump(config_dict, default_flow_style=False)
    print(out)
    
    try:
        response = query_yes_no("Would you like to commit changes?")
        if response:
            with open(zettaknight_globs.config_file_new, "w") as myfile:
                myfile.write(yaml.safe_dump(config_dict, default_flow_style=False))
                print(printcolors("changes committed", "OKGREEN"))
            
            ret[zettaknight_globs.fqdn]['Create Config']['0'] = {}
            ret[zettaknight_globs.fqdn]['Create Config']['0'] = out2
        else:
            print(printcolors("exit requested", "WARNING"))
            return
    except Exception as e:
        ret[zettaknight_globs.fqdn]['Create Config']['1'] = e
                
    return ret
 
def sharenfs(*args):
    '''
    Updates /etc/exports, runs exportfs -ar
    '''
    ret ={}
    
    if zettaknight_globs.help_flag:
        ret = """ShareNFS:

    Function to add entries in /etc/exports for provided dataset and iprange, and export the newly defined share.
    
    Usage:
        zettaknight sharenfs <dataset> <ip_range>

    Required Arguments:
        dataset
            The dataset to begin sharing
        ip_range
            The IP or IP_range to share provided dataset to."""

        return ret
            
    ret[zettaknight_globs.fqdn] = {}
    ret[zettaknight_globs.fqdn]['Create NFS Share'] = {}
    
    if len(args) != 2:
        ret[zettaknight_globs.fqdn]['Create NFS Share']['1'] = "sharenfs function takes exactly 2 arguments (dataset, ip_range)"
        parse_output(ret)
        return
    
    dataset = args[0]
    ip_range = args[1]
    
    #query datasets and verify provided dataset exists
    check_dset_cmd = "/sbin/zfs list -o name -H {0}".format(dataset)
    check_dset_run = spawn_job(check_dset_cmd)
    chk_code, chk_msg = check_dset_run.popitem()
    if int(chk_code) == 1:
        ret[zettaknight_globs.fqdn]['Create NFS Share']['1'] = "Provided dataset {0} does not exist.".format(dataset)
        parse_output(ret)
        return
    
    #Check if dataset already defined in /etc/exports
    check_share_cmd = "/bin/grep '^/{0}' /etc/exports".format(dataset)
    check_share_run = spawn_job(check_share_cmd)
    chk_code, chk_msg = check_share_run.popitem()
    if int(chk_code) == 1:
        #add share
        print("\n\nAdding share!\n\n")
        new_share_cmd = "/bin/echo /{0} {1}(rw,async,no_root_squash)".format(dataset, ip_range)
        new_share_tee = "tee -a /etc/exports"
        new_share_run = pipe_this(new_share_cmd, new_share_tee)
        new_share_run = {new_share_run.returncode : new_share_run.stdout.read()}
        chk_code, chk_msg = new_share_run.popitem()
        if int(chk_code) == 1:
            ret[zettaknight_globs.fqdn]['Create NFS Share']['1'] = chk_msg
            parse_output(ret)
            return
    else:
        if ip_range not in chk_msg:
            #append requested ip_range to existing share definition
            new_chk_msg = "{0},{1}(rw,async,no_root_squash)".format(chk_msg, ip_range)
            export_sed_cmd = "/bin/sed -i 's/{0}/{1}/' /etc/exports".format(chk_msg, new_chk_msg)
            export_sed_run = spawn_job(export_sed_cmd)
            chk_code, chk_msg = export_sed_run.popitem()
            if int(chk_code) == 1:
                ret[zettaknight_globs.fqdn]['Create NFS Share']['1'] = chk_msg
                parse_output(ret)
                return
    
    export_cmd = "/usr/sbin/exportfs -arv"
    ret[zettaknight_globs.fqdn]['Create NFS Share'] = spawn_job(export_cmd)
    
    return ret
 

def sharesmb(*args):
    '''
    needs to update a block of information for /etc/samba/smb.conf
    
    /etc/samba.conf
    [<share>]
    ...OPTIONS
    
    '''
    
    
    #smbpasswd -a <user>    
        
    
    return
 
def strip_input(msg):
    '''
    intended to strip the leading a trailing whitespace from passed in message
    '''
    
    if msg.startswith(" "):
          msg = msg[1:]
    if msg.endswith(" "):
        cut_index = len(msg) - 1
        msg = msg[:cut_index]
    
    return msg
 

def query_return_item(question):
    '''
    '''
    
    print(printcolors(str(question), "WARNING"))
    termios.tcflush(sys.stdin, termios.TCIOFLUSH)
    input = raw_input().lower()
    answer = strip_input(input)
    
    return answer
    
    
    

def query_return_list(question):
    '''
    '''
    
    resp_list = []
    
    print(printcolors("{0}".format(question), "WARNING"))
    print(printcolors("WARNING: Multiples entries separated by whitespace", "HEADER"))
    
    try:
        termios.tcflush(sys.stdin, termios.TCIOFLUSH)
        input = raw_input().lower()
        #print("query_return_list was given: {0}".format(input))
        resp_list = list(strip_input(input).split(" "))
        #print("returning: {0}".format(resp_list))
    except Exception as e:
        zlog("{0}".format(e), "CRITICAL")
        sys.exit(1)
    
    
    return resp_list
 
        
def query_yes_no(question, default="yes"):
    valid = {}
    valid['yes'] = True
    valid['no'] = False 
 
    if default is None:
        prompt = " [yes/no] "
    elif default == "yes":
        prompt = " [YES/no] "
    elif default == "no":
        prompt = " [yes/NO] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)
 
    while True:
        #sys.stdout.write(question + prompt)
        print(printcolors(str(question) + str(prompt), "WARNING"))
        choice = raw_input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            #print(valid[choice])
            return valid[choice]
        else:
            print(printcolors("Please respond with 'yes' or 'no'", "FAIL"))
 
def backup_files(*args):
    
    '''
    Accepts a list of files and backs them up to a zfs filesystem
    '''
    
    ret = {}
    
    if zettaknight_globs.help_flag:
        ret = """Backup Files:

    Function to backup Zettaknight configuration files, as well as other files relevant to pool and dataset functionality.
    ie. /etc/exports and /etc/crypttab 
    
    Usage:
        zettaknight backup_files"""

        return ret
        
    ret[zettaknight_globs.fqdn] = {}
    ret[zettaknight_globs.fqdn][zettaknight_globs.zettaknight_store] = {}
    ret[zettaknight_globs.fqdn][zettaknight_globs.zettaknight_store]['0'] = {}
    ret[zettaknight_globs.fqdn][zettaknight_globs.zettaknight_store]['1'] = {}
    
    
    zettaknight_store = zettaknight_globs.zettaknight_store
    
    if args:
        files = []
        for arg in args:
            files.append(arg)
    else:
        files = ["/etc/exports", "/etc/crypttab", "{0}".format(zettaknight_globs.config_file_new), zettaknight_globs.crypt_dir]
        
    try:
        gerp_run = spawn_job("/sbin/zfs list -H '{0}'".format(zettaknight_store))
        chk_code, chk_msg = gerp_run.popitem()
        if int(chk_code) is not 0:
        
            zlog("creating zettaknight store {0}".format(zettaknight_store), "INFO")
        
            zettaknight_zfs.add_dataset(zettaknight_store)
            
            zlog("created zettaknight store {0}".format(zettaknight_store), "SUCCESS")
        
        #backup files to store
        for file in files:
            destination_dir = "/{0}".format(zettaknight_globs.zettaknight_store) #add leading slash, zfs_share defined        
            filename = file.replace("/", "") #remove illegal characters from file path and save file as the concatenated version
            
            if os.path.isdir(destination_dir):
            
                if os.path.isfile(file):
                    #print("backing up {0} to {1}".format(file, destination_dir))
                    
                    zlog("copying file {0} to {1}".format(file, destination_dir), "INFO")
                    
                    shutil.copyfile(file, "{0}/{1}".format(destination_dir, filename))
                
                    zlog("copied file {0} to {1}".format(file, destination_dir), "SUCCESS")
                
                elif os.path.isdir(file):
                    if os.path.isdir("{0}/{1}".format(destination_dir, filename)):
                    
                        zlog("{0}/{1} already exists, removing copy any changes".format(destination_dir, filename), "WARNING")
                    
                        shutil.rmtree("{0}/{1}".format(destination_dir, filename))
                        
                    zlog("copying directory {0} to {1}".format(file, destination_dir), "INFO")
                    
                    shutil.copytree(file, "{0}/{1}".format(destination_dir, filename))
                    
                    zlog("copied directory {0} to {1}".format(file, destination_dir), "SUCCESS")
                    
                
                ret[zettaknight_globs.fqdn][zettaknight_globs.zettaknight_store]['0'] = "successfully backup up files to {0}\n{1}".format(destination_dir, files)
            else:
                ret[zettaknight_globs.fqdn][zettaknight_globs.zettaknight_store]['1'] = "{0} does not exist, cannot backup files".format(destination_dir)
        
    except Exception as e:
    
        zlog("{0}".format(e), "ERROR")
    
        zlog("{0}".format(e), "ERROR")
        ret[zettaknight_globs.fqdn][zettaknight_globs.zettaknight_store]['1'] = e
        
    return ret
    
def create_crond_file():
    
    crond_zettaknight = zettaknight_globs.crond_zettaknight
    crond_primary = zettaknight_globs.crond_primary
    crond_secondary = zettaknight_globs.crond_secondary
    
    ret = {}
    
    if zettaknight_globs.help_flag:
        ret = """Create Crond File:

    Function to create necessary crond files locally and remotely to schedule Zettaknight monitoring and management jobs.
    All necessary information is pulled from configuration files.
    
    Usage:
        zettaknight create_crond_file"""

        return ret
        
    ret[zettaknight_globs.fqdn] = {}
    ret[zettaknight_globs.fqdn][crond_zettaknight] = {}
    ret[zettaknight_globs.fqdn][crond_primary] = {}
    ret[zettaknight_globs.fqdn][crond_secondary] = {}
    
    
    ################## build zettaknight cron.d #######################
    ###################################################################
    try:
    
        zlog("building zettaknight essentials:\n\t{0}".format(crond_zettaknight), "INFO")
    
        with open(crond_zettaknight, "w") as myfile:
        
            zlog("[create_crond_file] opening file {0}".format(myfile), "DEBUG")
            
            cron_monitor = "root {0}/zettaknight.py zfs_monitor \"{1}\" &> /dev/null".format(zettaknight_globs.base_dir, zettaknight_globs.default_contact_info)
            cron_monitor_line = update_crond(cron_monitor, everyhour=1, minute=0)
            zlog("{0} --> {1}".format(cron_monitor_line, myfile), "DEBUG")
            myfile.write("{0}\n".format(cron_monitor_line))
            
            if _str_to_bool(zettaknight_globs.zettaknight_conf['parallel']):
                sync_monitor = "root {0}/zettaknight.py mail_error sync_all parallel=True &> /dev/null".format(zettaknight_globs.base_dir)
            else:
                sync_monitor = "root {0}/zettaknight.py mail_error sync_all &> /dev/null".format(zettaknight_globs.base_dir)
                
            sync_monitor_line = update_crond(sync_monitor, everyhour=1, minute=0)
            zlog("{0} --> {1}".format(sync_monitor_line, myfile), "DEBUG")
            myfile.write("{0}\n".format(sync_monitor_line))
            
            zettaknight_run = "root {0}/zettaknight.py mail_error &> /dev/null".format(zettaknight_globs.base_dir)
            zettaknight_run_line = update_crond(zettaknight_run, hour=23, minute=30)
            zlog("{0} --> {1}".format(zettaknight_run_line, myfile), "DEBUG")
            myfile.write("{0}\n".format(zettaknight_run_line))
            
            zpool_iostat = "root {0}/zettaknight.py mail_error generate_perf_stats &> /dev/null".format(zettaknight_globs.base_dir)
            zpool_iostat_line = update_crond(zpool_iostat, everyminute=5)
            zlog("{0} --> {1}".format(zpool_iostat_line, myfile), "DEBUG")
            myfile.write("{0}\n".format(zpool_iostat_line))
            
            enforce_config_run = "root {0}/zettaknight.py mail_error enforce_config &> /dev/null".format(zettaknight_globs.base_dir)
            enforce_config_run_line = update_crond(enforce_config_run, everyminute=10)
            zlog("{0} --> {1}".format(enforce_config_run_line, myfile), "DEBUG")
            myfile.write("{0}\n".format(enforce_config_run_line))
            
            enforce_zpool_config_run = "root {0}/zettaknight.py mail_error enforce_zpool_config &> /dev/null".format(zettaknight_globs.base_dir)
            enforce_zpool_config_run_line = update_crond(enforce_zpool_config_run, everyminute=10)
            zlog("{0} --> {1}".format(enforce_zpool_config_run_line, myfile), "DEBUG")
            myfile.write("{0}\n".format(enforce_zpool_config_run_line))
        
        with open(crond_zettaknight, "r") as myfile:
        
            zlog("[create_crond_file] opening file {0}".format(myfile), "DEBUG")

            out = myfile.read()  
        ret[zettaknight_globs.fqdn][crond_zettaknight]['0'] = "cron.d zettaknight built\n{0}".format(out)
                
    except Exception as e:
        zlog("{0}".format(e), "ERROR")
        ret[zettaknight_globs.fqdn][crond_zettaknight]['1'] = {}
        ret[zettaknight_globs.fqdn][crond_zettaknight]['1'] = e

    ###################################################################
    ###################################################################
    
    ############### build zettaknight primary #########################
    ###################################################################

    try:

        zlog("building local zettaknight owned datasets:\n\t{0}".format(crond_primary), "INFO")
    
        with open(crond_primary, "w") as myfile:
        
            zlog("[create_crond_file] opening file {0}".format(myfile), "DEBUG")
        
            for dataset in zettaknight_globs.zfs_conf.iterkeys():
                if 'snap' in zettaknight_globs.zfs_conf[dataset].iterkeys():
                    if 'interval' in zettaknight_globs.zfs_conf[dataset]['snap'].iterkeys():
                        arg_list = []
                        
                        cron_line = "root {0}/zettaknight.py mail_error zfs_maintain {1} &> /dev/null".format(zettaknight_globs.base_dir, str(dataset))
                            #arg_list.append(cron_line)
                        for cron_item in zettaknight_globs.zfs_conf[dataset]['snap']['interval']:
                            if isinstance(cron_item, dict):
                                for k, v in cron_item.iteritems():
                                    cron_string = "{0}={1}".format(k, v)
                                    arg_list.append(cron_string)
                            else:
                                arg_list.append(cron_item)
                        a, b = ' '.join(arg_list).split(" ")
                        var = update_crond(cron_line, a, b)
                        zlog("{0} --> {1}".format(var, myfile), "DEBUG")
                        myfile.write("{0}\n".format(var))
    
        with open(crond_primary, "r") as myfile:
            zlog("[create_crond_file] opening file {0}".format(myfile), "DEBUG")
            out1 = myfile.read()
            
        ret[zettaknight_globs.fqdn][crond_primary]['0'] = "cron.d primary datasets built\n{0}".format(out1)
        
        
    except Exception as e:
        zlog("{0}".format(e), "ERROR")
        ret[zettaknight_globs.fqdn][crond_primary]['1'] = {}
        ret[zettaknight_globs.fqdn][crond_primary]['1'] = e
                    
    ###################################################################
    ###################################################################            
   
    remote_cron_files = {}
    last_server = "some_string"
    
    try:                
        for dataset in zettaknight_globs.zfs_conf.iterkeys():
            for secondary, tertiary in zettaknight_globs.zfs_conf[dataset]['snap']['dgr'].iteritems():
                if remote_cron_files:
                    if secondary not in remote_cron_files.iterkeys():
                        remote_cron_files[secondary] = []
                else:
                    remote_cron_files[secondary] = []                        

                remote_user = zettaknight_globs.zfs_conf[dataset]['user']
                
                zettaknight_run = "root {0}/zettaknight.py mail_error &> /dev/null".format(zettaknight_globs.base_dir)
                zlog("[create_crond_file] --> update_crond:\n\t{0}".format(zettaknight_run), "DEBUG")
                zettaknight_run_line = update_crond(zettaknight_run, hour=23, minute=30)
                 
                if isinstance(tertiary, list):
                
                    zlog("tertiary variable {0} is a list for dataset {1}".format(tertiary, dataset), "DEBUG")
                    
                    for t in tertiary:
                        dgr_cron = "root {0}/zettaknight.py mail_error sync {1} {2}@{3} &> /dev/null\n".format(zettaknight_globs.base_dir, dataset, remote_user, t)
                        zlog("[create_crond_file] --> update_crond:\n\t{0}".format(dgr_cron), "DEBUG")
                        dgr_cron_line = update_crond(dgr_cron, everyhour=1, minute=30)
                        remote_cron_files[secondary].append(dgr_cron_line)
                else:
                        dgr_cron = "root {0}/zettaknight.py mail_error sync {1} {2}@{3} &> /dev/null\n".format(zettaknight_globs.base_dir, dataset, remote_user, tertiary)
                        zlog("[create_crond_file] --> update_crond:\n\t{0}".format(dgr_cron), "DEBUG")
                        dgr_cron_line = update_crond(dgr_cron, everyhour=1, minute=30)
                        remote_cron_files[secondary].append(dgr_cron_line)
            
            
            zlog("writing zettaknight essentials for each remote server defined", "INFO")
            
            if 'snap' in zettaknight_globs.zfs_conf[dataset].iterkeys():
                    if 'remote_server' in zettaknight_globs.zfs_conf[dataset]['snap'].iterkeys():
                        for remote_server in zettaknight_globs.zfs_conf[dataset]['snap']['remote_server']:
                            #print("remote_server:{0} last_server:{1}".format(remote_server, last_server))
                            if remote_server is not last_server:
                            
                                zlog("attempting to create {0} on remote server {1}".format(zettaknight_globs.crond_zettaknight, remote_server), "DEBUG")
                            
                                ssh = paramiko.SSHClient()
                                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                                ssh.connect(remote_server, username='root', key_filename=zettaknight_globs.identity_file)
                                sftp = ssh.open_sftp()
                                #write zettaknight crond file
                                
                                f = sftp.open(zettaknight_globs.crond_zettaknight, 'w')
                                
                                zlog("{0} --> {1}".format(cron_monitor_line, zettaknight_globs.crond_zettaknight), "DEBUG")
                                f.write("{0}\n".format(cron_monitor_line))
                                
                                zlog("{0} --> {1}".format(sync_monitor_line, zettaknight_globs.crond_zettaknight), "DEBUG")
                                f.write("{0}\n".format(sync_monitor_line))
                                
                                zlog("{0} --> {1}".format(zettaknight_run_line, zettaknight_globs.crond_zettaknight), "DEBUG")
                                f.write("{0}\n".format(zettaknight_run_line))
                                
                                zlog("{0} --> {1}".format(zpool_iostat_line, zettaknight_globs.crond_zettaknight), "DEBUG")
                                f.write("{0}\n".format(zpool_iostat_line))
                                
                                zlog("{0} --> {1}".format(enforce_config_run_line, zettaknight_globs.crond_zettaknight), "DEBUG")
                                f.write("{0}\n".format(enforce_config_run_line))
                                
                                zlog("{0} --> {1}".format(enforce_zpool_config_run_line, zettaknight_globs.crond_zettaknight), "DEBUG")
                                f.write("{0}\n".format(enforce_zpool_config_run_line))
                                
                                
                                f.close()
                                ssh.close()
                                last_server = remote_server
        
        if remote_cron_files:
            
            for server in remote_cron_files.iterkeys():
            
                zlog("writing secondary assignments in {0} for {1}".format(zettaknight_globs.crond_secondary, server), "INFO")
            
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(server, username='root', key_filename=zettaknight_globs.identity_file)
                sftp = ssh.open_sftp()
                #write zettaknight_secondary file for remote replication to tertiary
                f = sftp.open(zettaknight_globs.crond_secondary, 'w')
                for line in remote_cron_files[server]:
                    zlog("{0} --> {1}".format(line, zettaknight_globs.crond_secondary), "DEBUG")
                    f.write(line)
                f.close()
                ssh.close()
                
        ret[zettaknight_globs.fqdn][crond_secondary]['0'] = "Remote cron files created with the following data: \n    {0}".format(yaml.safe_dump(remote_cron_files, default_flow_style=False))
                
    except Exception as e:
        
        zlog("{0}".format(e), "ERROR")
        
        ret[zettaknight_globs.fqdn][crond_secondary]['1'] = str(e)
        pass
    
    zlog("ret from [create_crond_file]:\n\t{0}".format(ret), "DEBUG")
    return ret
    
def update_crond(line, *args, **kwargs):

    zlog("update_crond started, passed the following line:\n\t{0}".format(line), "DEBUG")
    
    ret = {}
    arg_list = []
    
    for arg in args:
        if "=" in arg:
            k, v = arg.split("=", 1)
            kwargs[k] = v
        else:
            arg_list.append(arg)
    
    cron_hour = "*"
    cron_min = "*"
    cron_day = "*"
    
    if 'hour' in kwargs.iterkeys():
        cron_hour = "{0}".format(kwargs['hour'])
    if 'everyhour' in kwargs.iterkeys():
        cron_hour = "*/{0}".format(kwargs['everyhour'])

    if 'minute' in kwargs.iterkeys():
        cron_min = "{0}".format(kwargs['minute'])
    if 'everyminute' in kwargs.iterkeys():
        cron_min = "*/{0}".format(kwargs['everyminute'])
    
    if 'day' in kwargs.iterkeys():
        cron_day = "{0}".format(kwargs['day'])
    if 'everyday' in kwargs.iterkeys():
        cron_day = "*/{0}".format(kwargs['everyday'])
        
    cron_time = "{0} {1} {2} * *".format(cron_min, cron_hour, cron_day)
    cron_line = "{0} {1}".format(cron_time, line)
    
    zlog("formatted cron line passed back from update_crond:\n\t{0}".format(cron_line), "DEBUG")
    return cron_line
    
        
def create_kwargs_from_args(*args):
    '''will parse kwargs when passed in with *args.  Not necessary if just kwargs or 
    just args.  Outputs in a dictionary format'''
    
    print(args)
    
    kwargs = {}
    arg_list = list(args)
    #print (arg_list)
    
    for arg in arg_list:
        print"inside loop: {0}".format(arg)
        if "=" in arg:
            print("saw an = in {0}".format(arg))
            k, v = arg.split("=", 1)
            kwargs[k] = v
            #arg_list.remove(arg)
            
    print("This is kwargs on create_kwargs_from_args : {0}".format(kwargs))
    return kwargs
 
def install_hpnssh(**kwargs):
    
    ret = {}

    ret = {}
    
    if zettaknight_globs.help_flag:
        ret = """Install HPNSSH:

    Function to attempt a basic install of HPNSSH.  (https://www.psc.edu/index.php/hpn-ssh)
        
    Usage:
        zettaknight install_hpnssh
        
    Optional Arguments:
        port
            Specifies a non-default port to listen for ssh connections on (default is 22)"""

        return ret
        
    ret[zettaknight_globs.fqdn] = {}
    ret[zettaknight_globs.fqdn]['install hpnssh'] = {}
    
    hpnssh_cmd = "{0}".format(zettaknight_globs.hpnssh_script)
    
    if 'port' in kwargs.iterkeys():
        port_num = kwargs['port']
        hpnssh_cmd = "{0} -n {1}".format(hpnssh_cmd, port_num)
 
    ret[zettaknight_globs.fqdn]['install hpnssh'] = spawn_job(hpnssh_cmd)
    
    return ret

def _str_to_bool(var):
    if isinstance(var, bool):
        return var

    if isinstance(var, str):
        if var.lower() == 'true':
            return True
        else:
            return False
            
    return None
    
def mm_post(message):
    '''
    '''
    import requests
    import json
    
    message = "\nServer: {0}\n{1}".format(zettaknight_globs.fqdn, message)
    payload = {}
    payload['username'] = "Zettaknight"
    payload['icon_url'] = zettaknight_globs.mm_icon
    payload['text'] = message
    headers = {'Content-Type': 'application/json'}
    try:
        r = requests.post(zettaknight_globs.mm_webhook, headers=headers, data='{0}'.format(json.dumps(payload)))
        print("Mattermost response: {0} {1}".format(r.status_code, r.reason))
    except Exception as e:
        print("Exception: {0}".format(e))
        pass
    
    return

