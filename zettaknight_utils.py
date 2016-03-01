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
import shutil
 
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
          ret = printcolors(e,"FAIL")
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
 
    mail_out_cmd = "bash {0} -s '{2}' -r '{3}' -m '{1}'".format(zettaknight_globs.mail_out_script, email_message, email_subject, email_recipient)
    ret = spawn_job(mail_out_cmd)
 
    return ret
 
def parse_output(out_dict):
    
    '''
    accepts information in the following format 
    ret[dataset]['job'][spawn_job]
    '''
    #goals
    #format a message
        #could be printed or emailed
    #caveats
        #parse output loops multiple times
    
    #zettaknight_globs.zfs_conf = _get_conf()
    
    #print("dictionary object passed to parse_output:\n{0}".format(out_dict))
    for dataset in out_dict.iterkeys():
        global_ret = ""
        mail_this = False
        a = printcolors("\nDataset: {0}\n────────┐".format(dataset), "HEADER")
        print(a)
        for job in out_dict[dataset].iterkeys():
            #print(printcolors("\t{0}:".format(job), "OKBLUE"))
            for exit_status, output in out_dict[dataset][job].iteritems():
                if isinstance(output, dict):
                    for value in out_dict[dataset][job][exit_status].itervalues():
                        for exit_status, output in value.iteritems():
                            #print("\n\noutput is : \n{0}\n\n ".format(output))
                            output = str(output.replace('\n', '\n\t\t\t   '))
                else:
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
            global_ret = "Zettaknight:\n{1}{2}".format(a, global_ret)
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
        returncode = 1
        ret = {returncode: e}
        print(printcolors(ret, "FAIL"))
        sys.exit(1)
 
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
        print(printcolors(e,"FAIL"))
        sys.exit(0)
        
    #arse_output(ret)
    
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
        
    #parse_output(ret)
    return ret
                
    
    
def check_quiet(quiet):
    
    if quiet:
        if str(quiet) is not "quiet":
            try:
                raise Exception("{0} argument not recognized by function: {1}".format(quiet, inspect.stack()[1][3]))
            except Exception as e:
                print(printcolors(e, "FAIL"))
                sys.exit(0)
            
    return quiet
 
 
def create_config(**kwargs):
    '''
    '''
    
    #print(kwargs)
    new_conf = {}
    
    #create var dictionary and depth
    var = {}
    var['snap'] = {}
    var['snap']['interval'] = {}
    var['snap']['remote_server'] = {}
    var['reservation'] = {}
    var['quota'] = {}
    var['secure'] = {}
    var['user'] = {} 
    var['retention'] = {}
    var['contact'] = {}
    
    
    
    
    dataset_list = []
    config_dict = zettaknight_globs.zfs_conf
        
    print(config_dict)
    
    #if a dataset is passed in, only do work for that particular dataset
    if 'dataset' in kwargs.iterkeys():
        print("a dataset was passed in : {0}").format(kwargs['dataset'])
        dataset = kwargs['dataset']
        dataset_list.append(dataset)
    else:
        if config_dict:
            for dset in config_dict.iterkeys():
                if not dset in dataset_list:
                    print("dataset {0} defined in configuration file, not in arguments. Adding to list".format(dset))
                    dataset_list.append(dset)
                        
    print("dataset_list = {0}".format(dataset_list))
                    
    for dataset in dataset_list:
        print(dataset)
        
        
        if str(dataset) in config_dict.iterkeys():
            print(printcolors("configuration for {0} exists, importing".format(dataset), "OKGREEN"))
            
            
            if 'snap' in config_dict[dataset].iterkeys():
                if 'interval' in config_dict[dataset]['snap'].iterkeys():
                    print(printcolors("interval imported {0}".format(config_dict[dataset]['snap']['interval']), "OKBLUE"))
                    var['snap']['interval'] = config_dict[dataset]['snap']['interval']
                
                if 'remote_server' in config_dict[dataset]['snap'].iterkeys():
                    print(printcolors("remote_server imported {0}".format(config_dict[dataset]['snap']['remote_server']), "OKBLUE"))
                    var['snap']['remote_server'] = config_dict[dataset]['snap']['remote_server']
                    
            if 'reservation' in config_dict[dataset].iterkeys():
                print(printcolors("reservation imported {0}".format(config_dict[dataset]['reservation']), "OKBLUE"))
                var['reservation'] = config_dict[dataset]['reservation']
                    
            if 'quota' in config_dict[dataset].iterkeys():
                print(printcolors("quota imported {0}".format(config_dict[dataset]['quota']), "OKBLUE"))
                var['quota'] = config_dict[dataset]['quota']
                
            if 'secure' in config_dict[dataset].iterkeys():    
                print(printcolors("secure imported {0}".format(config_dict[dataset]['secure']), "OKBLUE"))
                var['secure'] = config_dict[dataset]['secure']
                
            if 'user' in config_dict[dataset].iterkeys(): 
                print(printcolors("user imported {0}".format(config_dict[dataset]['user']), "OKBLUE"))
                var['user'] = config_dict[dataset]['user']
                 
            if 'retention' in config_dict[dataset].iterkeys():    
                print(printcolors("retention imported {0}".format(config_dict[dataset]['retention']), "OKBLUE"))
                var['retention'] = config_dict[dataset]['retention']
            
            if 'contact' in config_dict[dataset].iterkeys(): 
                print(printcolors("contact imported {0}".format(config_dict[dataset]['contact']), "OKBLUE"))
                var['contact'] = config_dict[dataset]['contact']
                
        else:
            print(printcolors("trying something else", "OKGREEN"))
            if 'interval' in kwargs.iterkeys():
                var['snap']['interval'] = kwargs['interval']
            else:
                var['snap']['interval'] = query_return_list("How often would you like zettaknight to run backups?\ni.e run every 4 hours [everyhour=4], to run at 10:30am, [hour=10]")
                    
            if 'remote_server' in kwargs.iterkeys():
                var['snap']['remote_server'] = kwargs['remote_server']
            else:
                var['snap']['remote_server'] = query_return_list("What server(s) do you want to replicate to? Will accept DNS names or IP addresses")
                    
            if 'reservation' in kwargs.iterkeys():
                var['reservation'] = kwargs['reservation']
            else:
                var['reservation'] = query_return_item("Enter reservation for {0}: ".format(dataset))
                
            if 'quota' in kwargs.iterkeys():
                var['quota'] = kwargs['quota']
            else:
                var['quota'] = query_return_item("Enter quota for {0}: ".format(dataset))
                
            if 'secure' in kwargs.iterkeys():
                var['secure'] = kwargs['secure']
            else:
                var['secure'] = query_yes_no("send snaps over ssh?: ")
                
            if 'user' in kwargs.iterkeys():
                var['user'] = kwargs['user']
            else:
                var['user'] = query_return_item("username for snapshot replication: ")
                
            if 'retention' in kwargs.iterkeys():
                var['retention'] = kwargs['retention']
            else:
                var['retention'] = query_return_item("How many days would you like zettaknight to keep snapshots for {0}: ".format(dataset))
                
            if 'contact' in kwargs.iterkeys():
                var['contact'] = kwargs['contact']
            else:
                var['contact'] = query_return_list("Who do you want zettaknight to contact when an error is encountered? [person1@example.com person2@example.com ...]")
 
        new_conf[str(dataset)] = var
        config_dict[str(dataset)] = var
                    
    print(printcolors("\n\n\nThe following changes will be made to {0}\n", "HEADER").format(zettaknight_globs.config_file_new))
    print(yaml.safe_dump(new_conf, default_flow_style=False))
 
    try:
        response = query_yes_no("Would you like to commit changes?")
        if response:
            conff = open(zettaknight_globs.config_file_new, 'w')
            ret = yaml.safe_dump(config_dict, conff, default_flow_style=False)
            #print(ret)
            conff.close()
            print(printcolors("changes committed", "OKGREEN"))
        else:
            print(printcolors("exit requested", "WARNING"))
            return
    except Exception as e:
        print(printcolors(e, "FAIL"))
        sys.exit(1)
 
    return
 
 
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
        print(printcolors(e, "FAIL"))
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
        if 'replace_line' in kwargs.iterkeys():
            cron_cmd = "{0} -r '{1}'".format(cron_cmd, str(kwargs['replace_line']))
            
        #print("command passed to cron script\n{0}".format(cron_cmd))
        
        ret = spawn_job(cron_cmd)
        if "Job succeeded" in ret.itervalues():
            ret['0'] = "Crontab updated with\n\t{0}".format(line)
    
    except Exception as e:
        print(printcolors(e, "FAIL"))
        sys.exit(0)
    
    #print(ret)
    return ret
    
def backup_files(*args):
    
    '''
    Accepts a list of files and backs them up to a zfs filesystem
    '''
    
    ret = {}
    ret[zettaknight_globs.fqdn] = {}
    ret[zettaknight_globs.fqdn][zettaknight_globs.zettaknight_store] = {}
    
    zettaknight_store = zettaknight_globs.zettaknight_store
    
    if args:
        files = []
        for arg in args:
            files.append(arg)
    else:
        files = ["/etc/exports", "/etc/crypttab", "{0}".format(zettaknight_globs.config_file_new), zettaknight_globs.crypt_dir, "{0}.pub".format(zettaknight_globs.identity_file)]
        
    try:
        if not os.path.isdir("/{0}".format(zettaknight_store)):
            gerp_run = zettaknight_utils.pipe_this2("/sbin/zfs list -H | /bin/grep {0}".format(zettaknight_store))
            if int(gerp_run.returncode) is not 0:
                zettaknight_zfs.add_dataset(zettaknight_store)
        
        
        #backup files to store
        for file in files:
            if os.path.exists(file):
                destination_dir = "/{0}/{1}".format(zettaknight_globs.zettaknight_store, zettaknight_globs.fqdn) #add leading slash, zfs_share defined
            if not os.path.isdir(destination_dir):
                    os.mkdir(destination_dir)
                    
            filename = file.replace("/", "") #remove illegal characters from file path and save file as the concatenated version
            
            if os.path.isfile(file):
                #print("backing up {0} to {1}".format(file, destination_dir))
                shutil.copyfile(file, "{0}/{1}".format(destination_dir, filename))
                
            elif os.path.isdir(file):
                if os.path.isdir("{0}/{1}".format(destination_dir, filename)):
                    shutil.rmtree("{0}/{1}".format(destination_dir, filename))
                shutil.copytree(file, "{0}/{1}".format(destination_dir, filename))
                
        ret[zettaknight_globs.fqdn][zettaknight_globs.zettaknight_store]['0'] = {}
        ret[zettaknight_globs.fqdn][zettaknight_globs.zettaknight_store]['0'] = "successfully backup up files to {0}\n{1}".format(destination_dir, files)
        
    except Exception as e:
        print(printcolors(e, "FAIL"))
        ret[zettaknight_globs.fqdn][zettaknight_globs.zettaknight_store]['1'] = {}
        ret[zettaknight_globs.fqdn][zettaknight_globs.zettaknight_store]['1'] = e
        
    return ret
    
def create_crond_file():
    
    ret = {}
    ret[zettaknight_globs.fqdn] = {}
    ret[zettaknight_globs.fqdn][zettaknight_globs.crond_file] = {}
    
    crond_file = zettaknight_globs.crond_file
    try:
        with open(crond_file, "w") as myfile:
    
            cron_monitor = "{0}/zettaknight.py zfs_monitor \"{1}\" &> /dev/null".format(zettaknight_globs.base_dir, zettaknight_globs.default_contact_info)
            var = update_crond(cron_monitor, everyhour=1, minute=0)
            myfile.write("{0}\n".format(var))

            sync_monitor = "{0}/zettaknight.py mail_error sync_all &> /dev/null".format(zettaknight_globs.base_dir)
            var = update_crond(sync_monitor, everyhour=1, minute=0)
            myfile.write("{0}\n\n".format(var))
    
            for dataset in zettaknight_globs.zfs_conf.iterkeys():
                if 'snap' in zettaknight_globs.zfs_conf[dataset].iterkeys():
                    if 'interval' in zettaknight_globs.zfs_conf[dataset]['snap'].iterkeys():
                        arg_list = []
                        cron_line = "{0}/zettaknight.py mail_error zfs_maintain {1} &> /dev/null".format(zettaknight_globs.base_dir, str(dataset))
                            #arg_list.append(cron_line)
                        for cron_item in zettaknight_globs.zfs_conf[dataset]['snap']['interval']:
                            if isinstance(cron_item, dict):
                                for k, v in cron_item.iteritems():
                                    cron_string = "{0}={1}".format(k, v)
                                    arg_list.append(cron_string)
                            else:
                                arg_list.append(cron_item)
                            #print("arg_list : {0}".format(arg_list))
                        a, b = ' '.join(arg_list).split(" ")
                        var = update_crond(cron_line, a, b)
                        myfile.write("{0}\n".format(var))
        
        #check to see if things are things
        with open(crond_file, "r") as myfile:
            out = myfile.read()    
            

        ret[zettaknight_globs.fqdn][zettaknight_globs.crond_file]['0'] = {}
        ret[zettaknight_globs.fqdn][zettaknight_globs.crond_file]['0'] = "cron.d built\n{0}".format(out)
    except Exception as e:
        print(printcolors(e, "FAIL"))
        ret[zettaknight_globs.fqdn][zettaknight_globs.crond_file]['1'] = {}
        ret[zettaknight_globs.fqdn][zettaknight_globs.crond_file]['1'] = e
        
    return ret
    
def update_crond(line, *args, **kwargs):
    
    ret = {}
    arg_list = []
    
    for arg in args:
        if "=" in arg:
            k, v = arg.split("=", 1)
            kwargs[k] = v
        else:
            arg_list.append(arg)
    
    crond_file = zettaknight_globs.crond_file
    
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
    
    hpnssh_cmd = "{0}".format(zettaknight_globs.hpnssh_script)
    
    if 'port' in kwargs.iterkeys():
        port_num = kwargs['port']
        hpnssh_cmd = "{0} -n {1}".format(hpnssh_cmd, port_num)
 
    ret = spawn_job(hpnssh_cmd)
    
    return ret
 
def create_store(store):
    '''
    this function is designed to create the zfs dataset necessary for zettaknight to pass
    it's configuration files around to non-primary nodes
    '''
    
    if not store:
        store = ""
    
    
    
#def check_dataset_exists(dataset):