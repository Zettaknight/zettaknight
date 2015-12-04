#!/usr/bin/python
# -*- coding: utf-8 -*-
# Import python libs


import sys
import logging
import subprocess
import shlex
import yaml
import os
import socket
import inspect
import datetime
import re
import termios

import zettaknight_globs


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


def mail_out(email_message, email_subject, email_recipient):
    '''
    multiple email recipients can be denoted as "<email 1> <email 2>"
    '''

    mail_out_cmd = "bash {0} -s '{2}' -r '{3}' -m '{1}'".format(zettaknight_globs.mail_out_script, email_message, email_subject, email_recipient)
    ret = spawn_job(mail_out_cmd)

    return ret

def parse_output(out_dict):
    #goals
    #format a message
        #could be printed or emailed
    #caveats
        #parse output loops multiple times
    
    #zettaknight_globs.zfs_conf = _get_conf()
    
    
    for dataset in out_dict.iterkeys():
        global_ret = ""
        mail_this = False
        a = printcolors("\nDataset: {0}\n────────┐".format(dataset), "HEADER")
        print(a)
        for job in out_dict[dataset].iterkeys():
            #print(printcolors("\t{0}:".format(job), "OKBLUE"))
            for exit_status, output in out_dict[dataset][job].iteritems():
                output = str(output.replace('\n', '\n\t\t\t   '))
                if str(exit_status) is "0":
                    task = "{0}".format(printcolors("\t├────────┬ {0}:".format(job),"OKBLUE"))
                    task_output = "{0}".format(printcolors("\t\t ├──────── {0}\n".format(output), "OKGREEN"))
                else:
                    if zettaknight_globs.mail_error_flag:
                        mail_this = True
						
                    task = "{0}".format(printcolors("\t├────────┬ {0}:".format(job), "OKBLUE"))
                    task_output = "{0}".format(printcolors("\t\t ├──────── {0}\n".format(output), "FAIL"))
					
                msg = "{0}\n{1}".format(task, task_output)
				
            global_ret = "{0}{1}\n".format(global_ret, msg)
			
        print(global_ret)
        
        if zettaknight_globs.mail_flag or mail_this:
            global_ret = "Job: {0}\n{1}{2}".format(str(inspect.stack()[1][3]), a, global_ret)
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

#    print(_printcolors("\033[0mnRunning command: {0}".format(cmd), "HEADER"))
    ret = {}
    try:
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
        ret = _printcolors(e,"FAIL")
        sys.exit(0)

    return ret

def ssh_keygen(keyfile, remote_ssh=False):
    '''
    '''
    
    import paramiko
    
    ret = {}
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
            if ssh_output:
                ret[zettaknight_globs.fqdn]['Generate SSH Key'] = {'0': "Nothing to do.\nKey authentication already setup for {0} with keyfile {1}".format(remote_ssh, keyfile)}
                parse_output(ret)
                return ret
        except Exception as e:
            pass
    
    try:
        ret[zettaknight_globs.fqdn]['Generate SSH Key'] = spawn_job(ssh_cmd)
    except Exception as e:
        print(printcolors(e,"FAIL"))
        sys.exit(0)
        
    parse_output(ret)
    
    return ret

def replace_keys(keyfile=False, delete=False):
    '''
    '''
    if not keyfile:
        source_id = zettaknight_globs.identity_file
        destination_id = '/tmp/zettaknight.id'
        os.rename(source_id, destination_id)
    else:
        source_id = keyfile
        
    ret = {}
    ret[zettaknight_globs.fqdn] = {}   
    ret[zettaknight_globs.fqdn]['Replace SSH Keys'] = {}
    
    for dataset in zettaknight_globs.zfs_conf.iterkeys():
        print(dataset)
        try:
            if zettaknight_globs.zfs_conf[dataset]['snap']['remote_server']:
                for server in zettaknight_globs.zfs_conf[dataset]['snap']['remote_server']:
                    ssh_keygen(source_id, "{0}@{1}".format(zettaknight_globs.zfs_conf[dataset]['user'], server))
            else:
                ssh_keygen(source_id)
        except Exception as e:
            print(printcolors(e,"FAIL"))
            sys.exit(0)
   
    ret[zettaknight_globs.fqdn]['Replace Luks Keys'] = {}
    
    luks_key_cmd = "bash {0} -k {1}".format(zettaknight_globs.luks_key_script, source_id)
    if delete:
        if str(delete) is not "-d":
            try:
                raise Exception("{0} argument not recognized by function: {1}".format(delete, inspect.stack()[0][3]))
            except Exception as e:
                print(printcolors(e, "FAIL"))
                sys.exit(0)
                
        luks_key_cmd = "{0} -k {1} -d".format(zettaknight_globs.luks_key_script, destination_id)
    
    try:
        if not keyfile:
            if os.path.exists(destination_id):
                os.remove(destination_id)
                #os.rename(new_keyfile, zettaknight_globs.identity_file)
        ret[zettaknight_globs.fqdn]['Replace Luks Keys'] = spawn_job(luks_key_cmd)
    except Exception as e:
        print(printcolors(e, "FAIL"))
        sys.exit(0)
    
    parse_output(ret)
    return ret

def backup_luks_headers(target=False):
    ret = {}
    ret[zettaknight_globs.fqdn] = {}
    
    #set location for luks header backups if empty
    if not target:
        target = zettaknight_globs.crypt_dir
    
    try:
        if target:
            luks_backup_cmd = "bash {0} -l {1}".format(zettaknight_globs.luks_header_backup_script, target)
            ret[zettaknight_globs.fqdn]['Backup Luks Headers'] = spawn_job(luks_backup_cmd)
    except Exception as e:
        ret[zettaknight_globs.fqdn]['1'] = e
        parse_output(ret)
        sys.exit(0)
        
    parse_output(ret)
    return ret
                
    
    
def check_quiet(quiet):
    
    if quiet:
        if str(quiet) is not "quiet":
            try:
                raise Exception("{0} argument not recognized by function: {1}".format(quiet, inspect.stack()[1][3]))
            except Exception as e:
                print(printcolors(e, "FAIL"))
                sys.exit(0)
            
    return


def create_config(**kwargs):
    '''
    '''
    
    print(kwargs)
    
    try:
        #kwargs = {}
        #arg_list = list(args)
    
        #for arg in arg_list[0:]:
        #    if "=" in arg:
        #        k, v = arg.split("=", 1)
        #        kwargs[k] = v
        #        arg_list.remove(arg)        

        #print("create conf kwargs : {0}".format(kwargs))
        #print(kwargs['dataset'])
    
        dataset_list = []
        
        #if a config file for the server exists, load it
        if os.path.isfile(zettaknight_globs.config_file):
            conff = open(zettaknight_globs.config_file, 'r')
            config_dict = yaml.safe_load(conff)
            conff.close()
        else:
            config_dict = {}
        
        #print(config_dict)
    
        #if a dataset is passed in, only do work for that particular dataset
        if 'dataset' in kwargs.iterkeys():
            #print("a dataset was passed in : {0}").format(kwargs['dataset'])
            dataset = kwargs['dataset']
            dataset_list.append(kwargs['dataset'])
        else:
            zfs_list_cmd = "/sbin/zfs list -o name -H"
            zfs_list_run = spawn_job(zfs_list_cmd)
            #print(zfs_list_run)
    
            if not zfs_list_run[0] == "Job succeeded":
                for dset in zfs_list_run[0].split("\n"):
                    #print(dset)
                    dataset_list.append(dset)
    
            if config_dict:
                for dset in config_dict.iterkeys():
                    #print(dset)
                    if not dset in dataset_list:
                        dataset_list.append(dset)
        
        #print(dataset_list)
        if 'interval' in kwargs.iterkeys():
            interval = kwargs['interval']
        else:
            interval = {}
            
        if 'remote_server' in kwargs.iterkeys():
            remote_server = kwargs['remote_server']
        else:
            remote_server = []
        
        if 'reservation' in kwargs.iterkeys():
            reservation = kwargs['reservation']
        else:
            reservation = ""
        
        if 'quota' in kwargs.iterkeys():
            quota = kwargs['quota']
        else:
            quota = ""
        
        if 'secure' in kwargs.iterkeys():
            secure = kwargs['secure']
        else:
            secure = ""
        
        if 'user' in kwargs.iterkeys():
            user = kwargs['user']
        else:
            user = ""
        
        if 'retention' in kwargs.iterkeys():
            retention = kwargs['retention']
        else:
            retention = ""
        
        if 'contact' in kwargs.iterkeys():
            contact = kwargs['contact']
        else:
            contact = []
 
             
        for dataset in dataset_list:
            #print(dataset)
            if dataset not in config_dict.iterkeys():
                new_conf = {}
                if dataset:
                    print(printcolors("\nConfiguration for {0}".format(dataset), "HEADER"))
                
                    dset = {}
                    dset['reservation'] = reservation
                    dset['quota'] = quota
                    dset['snap'] = {}
                    dset['snap']['remote_server'] = remote_server
                    dset['snap']['interval'] = interval
                    dset['retention'] = retention
                    dset['secure'] = secure
                    dset['user'] = user
                    dset['contact'] = contact
        
                    if not dset['reservation']:
                        termios.tcflush(sys.stdin, termios.TCIOFLUSH)
                        input = raw_input("Enter reservation for {0}: ".format(dataset))
                        dset['reservation'] = strip_input(input)
                    if not dset['quota']:
                        termios.tcflush(sys.stdin, termios.TCIOFLUSH)
                        input = raw_input("Enter quota for {0}: ".format(dataset))
                        dset['quota'] = strip_input(input)
                    if not dset['snap']['remote_server']:
                        print(printcolors("What server(s) do you want to replicate to? \nmultiple entries separated by whitespace, will accept DNS names or IP addresses\nex. [10.10.10.10 myserver.example.com]", "WARNING"))
                        termios.tcflush(sys.stdin, termios.TCIOFLUSH)
                        input = raw_input("replication server(s) {0}: ".format(dataset))
                        dset['snap']['remote_server'] = strip_input(input)
                        dset['snap']['remote_server'] = list(input.split(" "))
                        #var = query_return_list("Enter a snapshot replication server for {0}: ".format(dataset))
                        #dset['snap']['remote_server'] = var
                        
                    if not dset['snap']['interval']:
                        print(printcolors("How often would you like zettaknight to run backups?\ni.e run every 4 hours [everyhour=4], to run at 10:30am, [hour=10 minute=30]", "WARNING"))
                        termios.tcflush(sys.stdin, termios.TCIOFLUSH)
                        input = raw_input("Enter snapshot frequency for {0}: ".format(dataset))
                        input = strip_input(input)
                        dset['snap']['interval'] = list(input.split(" "))                  
                        
                        print("dset['snap']['interval'] is : {0}".format(dset['snap']['interval']))
                        if dset['snap']['interval']:
                            input_list = []
                            for interval in dset['snap']['interval']:
                                print("starting with {0} in interval".format(interval))
                                if ":" in interval:
                                    print("matched a : in {0}".format(interval))
                                    k,v = interval.split(":", 1)
                                    input_dict = {k: v}
                                    input_list.append(input_dict)
                                elif "=" in interval:
                                    print("matched a = in {0}".format(interval))
                                    k,v = interval.split("=", 1)
                                    input_dict = {k: v}
                                    input_list.append(input_dict)
                                #else:
                                #    input_list.append(interval)
                                    
                            dset['snap']['interval'] = input_list

                            

                        #dset['snap']['interval'] =                   
                        #input = raw_input("Enter snapshot frequency for {0}: ".format(dataset))
                        #dset['snap']['interval'] = strip_input(input)
                        #dset['snap']['interval'] = list(input.split(" "))
    
                    if not dset['retention']:
                        termios.tcflush(sys.stdin, termios.TCIOFLUSH)
                        print(printcolors("How many days would you like zettaknight to keep snapshots for {0}: ".format(dataset), "WARNING"))
                        input = raw_input("snapshot retention time for {0}?: ".format(dataset))
                        dset['retention'] = strip_input(input)
        
                    if not dset['secure']:
                        termios.tcflush(sys.stdin, termios.TCIOFLUSH)
                        input = raw_input("send snaps over ssh? False will require xinetd <True/False>: ")
                        dset['secure'] = strip_input(input)
                    if not dset['user']:
                        termios.tcflush(sys.stdin, termios.TCIOFLUSH)
                        input = raw_input("username for snapshot replication: ")
                        dset['user'] = strip_input(input)
                    if not dset['contact']:
                        print(printcolors("Who do you want zettaknight to contact when an error is encountered? [person1@example.com person2@example.com ...]", "WARNING"))
                        termios.tcflush(sys.stdin, termios.TCIOFLUSH)
                        input = raw_input("contact email address: ")
                        dset['contact'] = strip_input(input)
                        dset['contact'] = list(input.split(" "))
                
                    config_dict[str(dataset)] = dset
                    new_conf[str(dataset)] = dset
                    
                    print(printcolors("\n\n\nThe following changes will be made to {0}\n", "HEADER").format(zettaknight_globs.config_file))
                    print(yaml.safe_dump(new_conf, default_flow_style=False))
        
                    response = query_yes_no("Would you like to commit changes?")
                    if not response:
                        sys.exit(0)
        
    

                    conff = open(zettaknight_globs.config_file, 'w')
                    ret = yaml.safe_dump(config_dict, conff, default_flow_style=False)
                    #print(ret)
                    conff.close()
                    print(printcolors("changes committed", "OKGREEN"))
            else:
                print(printcolors("\nnothing to do, {0} defined in {1}".format(dataset, zettaknight_globs.config_file), "WARNING"))
    except Exception as e:
        print(printcolors(e, "FAIL"))


def sharenfs(*args):
    '''
    Updates /etc/exports, runs exportfs -ar
    '''
    ret ={}
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
    parse_output(ret)
    
    return


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


def query_return_list(question):
    '''
    '''
    resp_list = []
    
    while True:
        print(printcolors(str(question), "WARNING"))
        choice = raw_input().lower()
        if choice is not None and choice != '':
            resp_list.append(strip_input(choice))
        else:
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
            
            
def collect_metrics():
    '''
    This function will collect all usage information for each dataset defined
    on a system and report back in a stand convention to be used in other
    functions
    '''

    
def update_cron(line, *args, **kwargs):
    '''
    '''
    

    arg_list = []
    
    for arg in args:
        if "=" in arg:
            k, v = arg.split("=", 1)
            kwargs[k] = v
        else:
            arg_list.append(arg)
            
#    line = arg_list[0]
#    line = arg_list[0]
    
    #print("args : {0} and kwargs : {1} passed to update_cron".format(arg_list, kwargs))
    #print("line to be added to crontab : {0}".format(line))
    
#    ret = {}
#    ret[zettaknight_globs.fqdn] = {}
    
    try:
        cron_cmd = "bash {0} -l '{1}'".format(zettaknight_globs.update_cron_script, line)
        if 'hour' in kwargs.iterkeys():
            cron_cmd = "{0} -h {1}".format(cron_cmd, kwargs['hour'])
        if 'everyhour' in kwargs.iterkeys():
            cron_cmd = "{0} -H {1}".format(cron_cmd, kwargs['everyhour'])
        if 'minute' in kwargs.iterkeys():
            cron_cmd = "{0} -m {1}".format(cron_cmd, kwargs['minute'])
        if 'everyminute' in kwargs.iterkeys():
            cron_cmd = "{0} -M {1}".format(cron_cmd, kwargs['everyminute'])
        if 'day' in kwargs.iterkeys():
            cron_cmd = "{0} -d {1}".format(cron_cmd, kwargs['day'])
        if 'everyday' in kwargs.iterkeys():
            cron_cmd = "{0} -D {1}".format(cron_cmd, kwargs['everyday'])
        
        cron_out = spawn_job(cron_cmd)
        if "Job succeeded" in cron_out.itervalues():
            cron_out['0'] = "Crontab updated with\n\t{0}".format(line)
            
        ret = cron_out
        #parse_output(ret)
    
    except Exception as e:
        print(printcolors(e, "FAIL"))
        sys.exit(0)
    
    #print(ret)
    return ret
        
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
