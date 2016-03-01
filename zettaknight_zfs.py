#!/usr/bin/python
# -*- coding: utf-8 -*-
# Import python libs
 
import inspect
import re
import sys
import fileinput
 
#from zettaknight import *
import zettaknight_utils
import zettaknight_globs
 
def nuke(pool, force=True):
    '''
    '''
    ret = {}
    ret[pool] = {}
    ret[pool]['Nuke Zpool'] = {}
 
    nuke_cmd = "bash {0} -p '{1}'".format(zettaknight_globs.zfs_nuke_script, pool)
    if force:
        nuke_cmd = "{0} -f".format(nuke_cmd)
    ret[pool]['Nuke Zpool'] = zettaknight_utils.spawn_job(nuke_cmd)
    #zettaknight_utils.parse_output(ret)
 
    return ret
 
def failover(dataset, remote_server=False):
    '''
    '''
    ret = {}
    ret[dataset] = {}
    ret[dataset]['Failover'] = {}
 
    try:
        user = zettaknight_globs.zfs_conf[dataset]['user']
        secure = zettaknight_globs.zfs_conf[dataset]['secure']
    except Exception as e:
        ret[dataset]['Failover']['1'] = "Dataset: {0} not configured in configuration file.".format(dataset)
        zettaknight_utils.parse_output(ret)
        sys.exit(0)
 
    try:
        if not remote_server:
            remote_server = zettaknight_globs.zfs_conf[dataset]['snap']['remote_server']
            if isinstance(remote_server, list):
                if len(remote_server) > 1:
                    raise Exception("Multiple remote servers defined in configuration.")
    except Exception as e:
        ret[dataset]['Failover']['1'] = "{0}\nRemote servers defined:\n - {1}\nRe-run with explicit remote server to failover to.".format(e, list(zettaknight_globs.zfs_conf[dataset]['snap']['remote_server']))
        zettaknight_utils.parse_output(ret)
        sys.exit(0)
 
    snap_cmd = "bash {0} -d {1} -s {2}@{3} -i {4} -f".format(zettaknight_globs.snap_script, dataset, user, remote_server[0], zettaknight_globs.identity_file)
    if secure:
        snap_cmd = "{0} -e".format(snap_cmd)
 
    ret[dataset]['Failover'] = zettaknight_utils.spawn_job(snap_cmd)
    zettaknight_utils.parse_output(ret)
 
    return ret
 
 
def scrub(pool):
    '''
    initiates a scrub of the pool
    '''
 
    ret = {}
    ret[pool] = {}
    ret[pool]['Scrub'] = {}
    scrub_cmd = "/sbin/zpool scrub {0}".format(pool)
    scrub_run = zettaknight_utils.spawn_job(scrub_cmd)
    for k,v in scrub_run.iteritems():
        if str(k) is "0":
            ret[pool]['Scrub']['0'] = "Scrub initiated."
        else:
            ret[pool]['Scrub']['1'] = v
 
    zettaknight_utils.parse_output(ret)
 
    return ret
 
 
def take_snap(dataset, user, remote_server, secure, nosnap=False, pull_snap=False):
    '''
    '''
 
    snap_cmd = "bash {0} -d {1} -i {2} -s {3}@{4}".format(zettaknight_globs.snap_script, dataset, zettaknight_globs.identity_file, user, remote_server)
    if secure:
        snap_cmd = "{0} -e".format(snap_cmd)
 
    if nosnap:
        snap_cmd = "{0} -r".format(snap_cmd)
    
    if pull_snap:
        snap_cmd = "{0} -p".format(snap_cmd)
 
    print("SNAP_COMMAND: {0}".format(snap_cmd))
    ret = zettaknight_utils.spawn_job(snap_cmd)
 
    return ret
 
 
 
def create_snap(dataset, quiet=False):
    '''
    '''
 
    zettaknight_utils.check_quiet(quiet)
 
    snap = "{0}@{1}".format(dataset, zettaknight_globs.today_date)
    gerp_run = zettaknight_utils.pipe_this2("/sbin/zfs list -r -t snapshot -o name -H {0} | /bin/grep {1}".format(dataset, snap))
    gerp_out = gerp_run.stdout.read()
 
    if int(gerp_run.returncode) is not 0:
        ret = zettaknight_utils.spawn_job("/sbin/zfs snapshot -r {0}".format(snap))
 
    if int(gerp_run.returncode) == 0:
        ret = {0: "Snapshot {0} already exists.".format(snap)}
 
    for exit_status, output in ret.iteritems():
        if str(exit_status) == "0" and str(output) == "Job succeeded":
            ret[exit_status] = "Snapshot created: {0}".format(snap)
 
    if not quiet:
        snap_out = {}
        snap_out[dataset] = {}
        snap_out[dataset][inspect.stack()[0][3]] = ret
        zettaknight_utils.parse_output(snap_out)
 
    return ret
 
 
def set_quota(dataset, quota):
    '''
    '''
 
    #quota_cmd = "bash {0} -d {1} -q {2}".format(zettaknight_globs.quota_script,dataset,quota)
    quota_cmd = "/sbin/zfs set quota={0} {1}".format(quota, dataset)
    
    ret = {}
    ret[dataset] = {}
    ret[dataset]['Quota'] = zettaknight_utils.spawn_job(quota_cmd)
    
    for exit_status, output in ret[dataset]['Quota'].iteritems():
        if "Job succeeded" in output:
            ret[dataset]['Quota'][exit_status] = "quota set to {0}".format(quota)
 
    return ret
 
def set_refquota(dataset, refquota):
    '''
    '''
    
    refquota_cmd = "/sbin/zfs set refquota={0} {1}".format(refquota, dataset)
    
    ret = {}
    ret[dataset] = {}
    ret[dataset]['refquota'] = zettaknight_utils.spawn_job(refquota_cmd)
    
    for exit_status, output in ret[dataset]['refquota'].iteritems():
        if "Job succeeded" in output:
            ret[dataset]['refquota'][exit_status] = "refquota set to {0}".format(refquota)
 
    return ret
 
    
def set_reservation(dataset, reservation, quiet=False):
    '''
    '''
 
    zettaknight_utils.check_quiet(quiet)
 
    #reservation_cmd = "bash {0} -d {1} -r {2}".format(zettaknight_globs.quota_script,dataset,reservation)
    reservation_cmd = "/sbin/zfs set reservation={0} {1}".format(reservation, dataset)
    
    
    ret = {}
    ret[dataset] = {}
    ret[dataset]['Reservation'] = zettaknight_utils.spawn_job(reservation_cmd)
              
    for exit_status, output in ret[dataset]['Reservation'].iteritems():
        if "Job succeeded" in output:
            ret[dataset]['Reservation'][exit_status] = "reservation set to {0}".format(reservation)
 
    return ret
 
def set_refreservation(dataset, refreservation):
    '''
    '''
    
    refreservation_cmd = "/sbin/zfs set refreservation={0} {1}".format(refreservation, dataset)
    
    ret = {}
    ret[dataset] = {}
    ret[dataset]['refreservation'] = zettaknight_utils.spawn_job(refreservation_cmd)
    
    for exit_status, output in ret[dataset]['refreservation'].iteritems():
        if "Job succeeded" in output:
            ret[dataset]['refreservation'][exit_status] = "refreservation set to {0}".format(refreservation)
 
    return ret
 
 
def cleanup_snaps(dataset, retention):
    '''
    '''
 
    cleanup_cmd = "bash {0} -d {1} -k {2}".format(zettaknight_globs.cleanup_script, dataset, retention)
    ret = zettaknight_utils.spawn_job(cleanup_cmd)
 
    return ret
 
def sync(dataset, remote_ssh, identity_file=False, pull_snap=False):
    '''
    '''
    
    sync_cmd = "bash {0} -d {1} -s {2}".format(zettaknight_globs.sync_script, dataset, remote_ssh)
    
    if identity_file:
        sync_cmd = "{0} -i {1}".format(sync_cmd, identity_file)
    if pull_snap:
        sync_cmd = "{0} -p".format(sync_cmd)
    
    if str(inspect.stack()[1][3]) is 'sync_all':
        ret = zettaknight_utils.spawn_job(sync_cmd)
    else:
        ret = {}
        ret[dataset] = {}
        ret[dataset]['Snapshot sync'] = zettaknight_utils.spawn_job(sync_cmd)
    
    return ret
 
def sync_all():
    '''
    '''
    
    ret = {}
    protocol = "ssh"
    
    for dataset in zettaknight_globs.zfs_conf.iterkeys():            
        ret[dataset] = {}
        if 'snap' in zettaknight_globs.zfs_conf[dataset].iterkeys():
            if zettaknight_globs.zfs_conf[dataset]['snap']:
                if 'remote_server' in zettaknight_globs.zfs_conf[dataset]['snap'].iterkeys():
                    for remote_server in zettaknight_globs.zfs_conf[dataset]['snap']['remote_server']:
                        try:    
                            if str(zettaknight_globs.zfs_conf[dataset]['primary']) != str(zettaknight_globs.fqdn):
                                if str(zettaknight_globs.zfs_conf[dataset]['primary']) == str(remote_server):
                                    pull_snap = True
                                else:
                                    pull_snap = False
                            else:
                                pull_snap = False
                                                            
                        except KeyError:
                            pull_snap = False
                            pass    
                        
                        ret[dataset]['Snapshot sync with {0}'.format(remote_server)] = sync(dataset, "{0}@{1}".format(zettaknight_globs.zfs_conf[dataset]['user'], remote_server), zettaknight_globs.identity_file, pull_snap)
                    
    return ret
 
def rename_dataset(**kwargs):
    '''
    '''
    
    import paramiko
    
    try: 
        
        conf_file = zettaknight_globs.config_file_new
        
        if not 'keyfile' in kwargs.iterkeys():
            keyfile = zettaknight_globs.identity_file
        
        if not 'dataset' in kwargs.iterkeys():
            raise ValueError('A very specific bad thing happened')
            #required argument, show_help
        else:
            dataset = kwargs['dataset']
        
        if not 'new_dataset' in kwargs.iterkeys():
            #required argument, show_help
            raise ValueError('A very specific bad thing happened')
        else:
            new_dataset = kwargs['new_dataset']
            
        if not 'user' in kwargs.iterkeys():
            user = zettaknight_globs.zfs_conf[dataset]['user']
            print("user is {0}".format(user))
            
        remote_server = []
        for r_server in zettaknight_globs.zfs_conf[dataset]['snap']['remote_server']:
            remote_server.append(r_server)
            print(remote_server)
    
    except Exception as e:
        print(zettaknight_utils.printcolors(e, "FAIL"))
        sys.exit(1)
        
    ret = {}
    ret[zettaknight_globs.fqdn] = {}
    ret[zettaknight_globs.fqdn]['rename {0}'.format(dataset)] = {}
    
    try:
        for r in remote_server:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(r, username=user, key_filename=keyfile)
            remote_sudo_cmd = "zfs rename {0} {1}".format(dataset, new_dataset)
            ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(remote_sudo_cmd)  
            print ssh_stdout.read()
 
        #call function replace_string
        replace_string(dataset, new_dataset, conf_file)
 
        cmd = "zfs rename {0} {1}".format(dataset, new_dataset)
        zettaknight_utils.spawn_job(cmd)
    except Exception as e:
        print(zettaknight_utils.printcolors(e, "FAIL"))
        sys.exit(1)
        
        
    ret[zettaknight_globs.fqdn]['rename {0}'.format(dataset)] = {0 : "successfully renamed {0} to {1}, all records have been updated".format(dataset, new_dataset)}
    
    return ret
    
 
def replace_string(string, new_string, file):
    '''
    function is take a given string, replace with another string in a specified file
    '''
    
    ret = {}
    ret[zettaknight_globs.fqdn] = {}
    
    try:
        string = str(string)
        new_string = str(new_string)
    
        for line in fileinput.input(file, inplace=1):
            if string in line:
                line = line.replace(string,new_string)
                ret = "replaced {0} with {1}".format(string, line)
                #ret[zettaknight_globs.fqdn]['replace_string'] = {0 : "replaced {0} with {1}".format(string, line)}
            sys.stdout.write(line)
    except Exception as e:
        print(printcolors(e, "FAIL"))
        sys.exit(1)
        
    return ret
    
    #rename secondary target
 
def check_usage(dset=False, quiet=False):
    '''
    '''
    ret = {}
    zettaknight_utils.check_quiet(quiet)
 
    if dset and str(dset) not in zettaknight_globs.zfs_conf.iterkeys():
        ret[dset] = {}
        ret[dset]['Check Usage'] = {1: "{0} is not a Zettaknight controlled dataset.".format(dset)}
        zettaknight_utils.parse_output(ret)
        return ret
 
    for dataset in zettaknight_globs.zfs_conf.iterkeys():
        if dset:
            if str(dset) != str(dataset):
                continue
 
        ret[dataset] = {}
        ret[dataset]['Check Usage'] = {}
        quota = zettaknight_globs.zfs_conf[dataset]['quota']
        reservation = zettaknight_globs.zfs_conf[dataset]['reservation']
 
        #find conversion multiplier to convert reservation to bytes
        if 'G' in reservation:
            res_x = float(1073741824)
            res_unit = "G"
        if 'T' in reservation:
            res_x = float(1099511627776)
            res_unit = "T"
        if 'M' in reservation:
            res_x = float(1048576)
            res_unit = "M"
        if str(reservation) == 'none':
            res_x = float(1073741824)
            res_unit = "G"
 
        contact = zettaknight_globs.zfs_conf[dataset]['contact']
 
        check_usage_cmd = "/sbin/zfs list -ro space {0} -H -p".format(dataset)
        check_usage_run = zettaknight_utils.spawn_job(check_usage_cmd)
        chk_code, chk_msg = check_usage_run.popitem()
        chk_msg = re.sub("\n", "", chk_msg)
        chk_msg_split = chk_msg.split("\t")
 
        if not str(chk_code) == "0":
            ret[dataset]['Check Usage']['1'] = "{0}Verify correct datasets are defined in configuration file\n".format(re.sub("[\[\"\]]", "", str(chk_msg_split)))
            continue
 
        if str(chk_msg_split[0]) == str(dataset):
            avail = float(re.sub("[A-Za-z]", "", chk_msg_split[1])) #space available for dataset
            used = float(re.sub("[A-Za-z]", "", chk_msg_split[2])) #how much space is used by the dataset
            usnap = float(re.sub("[A-Za-z]", "", chk_msg_split[3])) #how much of the used space is consumed by snapshots
            uds = float(re.sub("[A-Za-z]", "", chk_msg_split[4])) #how much of the space is consumed by the dataset itself
            if str(reservation) != 'none':
                res = (float(re.sub("[A-Za-z]", "", reservation)) * res_x)
 
            avail_friendly = "{0:.2f}{1}".format((avail / res_x), res_unit)
            used_friendly = "{0:.2f}{1}".format((used / res_x), res_unit)
            usnap_friendly = "{0:.2f}{1}".format((usnap / res_x), res_unit)
            uds_friendly = "{0:.2f}{1}".format((uds / res_x), res_unit)
            if "e-" in str(used_friendly):
                used_friendly = "{0}{1}".format(int(0), res_unit)
            if "e-" in str(usnap_friendly):
                usnap_friendly = "{0}{1}".format(int(0), res_unit)
            if "e-" in str(uds_friendly):
                uds_friendly = "{0}{1}".format(int(0), res_unit)
 
            if str(reservation) != 'none' and used > res:
                a = "{0}: {1}\n\t\t".format(zettaknight_utils.printcolors("Dataset", "OKBLUE"),zettaknight_utils.printcolors(dataset, "FAIL"))
                b = "{0}: {1}\n{2}: {3}\n{4}: {5}\n{6}: {7}".format(zettaknight_utils.printcolors("Reservation", "OKBLUE"),zettaknight_utils.printcolors(reservation, "OKGREEN"),zettaknight_utils.printcolors("Total Used", "OKBLUE"),zettaknight_utils.printcolors(used_friendly, "WARNING"),zettaknight_utils.printcolors("Used by Snapshots", "OKBLUE"),zettaknight_utils.printcolors(usnap_friendly, "WARNING"),zettaknight_utils.printcolors("Active Dataset size", "OKBLUE"),zettaknight_utils.printcolors(uds_friendly, "WARNING"))
                c = zettaknight_utils.printcolors("\nDataset exceeds space reservation", "WARNING")
                msg = "{0}{1}{2}".format(a, b, c)
                ret[dataset]['Check Usage']['1'] = "{0}{1}".format(b, c)
            else:
                a = "{0}: {1}\n\t\t".format(zettaknight_utils.printcolors("Dataset", "OKBLUE"),zettaknight_utils.printcolors(dataset, "OKGREEN"))
                b = "{0}: {1}\n{2}: {3}\n{4}: {5}\n{6}: {7}".format(zettaknight_utils.printcolors("Reservation", "OKBLUE"),zettaknight_utils.printcolors(reservation, "OKGREEN"),zettaknight_utils.printcolors("Total Used", "OKBLUE"),zettaknight_utils.printcolors(used_friendly, "OKGREEN"),zettaknight_utils.printcolors("Used by Snapshots", "OKBLUE"),zettaknight_utils.printcolors(usnap_friendly, "OKGREEN"),zettaknight_utils.printcolors("Active Dataset size", "OKBLUE"),zettaknight_utils.printcolors(uds_friendly, "OKGREEN"))
                msg = "{0}{1}".format(a, b)
                ret[dataset]['Check Usage']['0'] = b
    
    return ret
 
 
def add_dataset(*args, **kwargs):
    '''if create_config=True is passed, a configuration file
    will be created for the dataset passed in to this function'''
 
 
    #kwargs = {}
    arg_list = list(args)
 
    #kwargs = zettaknight_utils.create_kwargs_from_args(arg_list)
    #print("This is kwargs : {0}".format(kwargs))
 
    for arg in arg_list[0:]:
        if "=" in arg:
            k, v = arg.split("=", 1)
            kwargs[k] = v
            arg_list.remove(arg)
 
    dataset = arg_list[0]
    ret = {}
    ret[dataset] = {}
    
    gerp_run = zettaknight_utils.pipe_this2("zfs list | /bin/grep {0}".format(dataset))
    gerp_out = gerp_run.stdout.read()
    
    
    if 'create_config' not in kwargs.iterkeys():
        kwargs['create_config'] = True
        
    if kwargs['create_config'] == 'False':
        kwargs['create_config'] == False
        
    if kwargs['create_config']:
        print(zettaknight_utils.printcolors("\nWill create {0} after completion of config file\n".format(dataset), "OKGREEN"))
        conf_dict = {'dataset' : dataset}
        zettaknight_utils.create_config(**conf_dict)
    
    #create dataset after commit of file
    if int(gerp_run.returncode) is not 0:
        create_cmd = "zfs create -p {0}".format(dataset)
        create_run = zettaknight_utils.spawn_job(create_cmd)
        ret[dataset]['add_dataset'] = create_run
    else:
        ret[dataset]['add_dataset'] = {'0' : "{0} exists".format(dataset)}
        
    question = zettaknight_utils.query_yes_no("Would you like to create an NFS share for: {0}".format(dataset))
    if question:
        nfs_share = zettaknight_utils.query_return_item("Where would you like to share it? <i.e 10.20.30.1/24 or my.server>")
        zettaknight_utils.sharenfs(dataset, nfs_share)
 
    #zettaknight_utils.parse_output(ret)
 
    return ret
 
 
def configure_replication(dset=False):
    '''
    Setup secondary servers defined in conf file.
    Verifies ssh-keys, permissions, sudo access, etc.
    '''
 
    import paramiko
 
    paramiko.util.log_to_file('ssh.log') # sets up logging
 
    ret = {}
 
    if not dset:
        dset = zettaknight_globs.zfs_conf.iterkeys()
 
    for dataset in zettaknight_globs.zfs_conf.iterkeys():
        if dataset in dset:
            ret[dataset] = {}
            try:
                if 'user' in zettaknight_globs.zfs_conf[dataset].iterkeys():
                    user = zettaknight_globs.zfs_conf[dataset]['user']
            except Exception as e:
                user = 'root'
                pass
 
            if 'snap' in zettaknight_globs.zfs_conf[dataset].iterkeys():
                if zettaknight_globs.zfs_conf[dataset]['snap']:
                    if 'remote_server' in zettaknight_globs.zfs_conf[dataset]['snap'].iterkeys():
                        for remote_server in zettaknight_globs.zfs_conf[dataset]['snap']['remote_server']:
                            try:
                                ret[dataset]['Configure {0}'.format(remote_server)] = {}
                                remote_ssh = "{0}@{1}".format(user, remote_server)
                                zettaknight_utils.ssh_keygen(zettaknight_globs.identity_file, remote_ssh)
                            except Exception as e:
                                ret[dataset]['Configure {0}'.format(remote_server)]['1'] = "Key generation failed with error: {0}".format(e)
                                break
 
                            if user != 'root':
                                remote_ssh = "{0}@{1}".format('root', remote_server)
                                zettaknight_utils.ssh_keygen(zettaknight_globs.identity_file, remote_ssh)
                                zettaknight_utils.ssh_keygen(zettaknight_globs.identity_file, 'root@127.0.0.1')
                                sudo_add_cmd = "/bin/echo '{0} ALL=(ALL) NOPASSWD:/sbin/zfs,/sbin/service' | (EDITOR='/usr/bin/tee -a' /usr/sbin/visudo)".format(user)
                                try:
                                    ssh = paramiko.SSHClient()
                                    #########################################################
                                    #if you don't have the remote server's key in known hosts, this sets the policy to add it. It will break if key has changed
                                    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                                    #########################################################
 
                                    ssh.connect('127.0.0.1', username='root', key_filename=zettaknight_globs.identity_file)
                                    remote_sudo_cmd = '/bin/echo "{0} ALL=(ALL) NOPASSWD:/sbin/zfs,/sbin/service" | (EDITOR="/usr/bin/tee -a" /usr/sbin/visudo)'.format(user)
                                    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(remote_sudo_cmd)
                                    ssh.close()
                                except Exception as e:
                                    ret[dataset]['Configure {0}'.format(remote_server)]['1'] = "Configuration failed with error: {0}".format(e)
                                    break
 
                                try:
                                    ssh2 = paramiko.SSHClient()
                                    ssh2.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                                    ssh2.connect(remote_server, username='root', key_filename=zettaknight_globs.identity_file)
                                    remote_sudo_cmd = "echo '{0} ALL=(ALL) NOPASSWD:/sbin/zfs,/sbin/service' | (EDITOR='/usr/bin/tee -a' /usr/sbin/visudo)".format(user)
                                    ssh2_stdin, ssh2_stdout, ssh2_stderr = ssh2.exec_command(remote_sudo_cmd)
                                    remote_sudo_cmd = "zfs unmount {0} && zfs set readonly=on {0} && zfs mount {0}".format(dataset)
                                    ssh2_stdin, ssh2_stdout, ssh2_stderr = ssh2.exec_command(remote_sudo_cmd)                               
                                    ssh2.close()
                                except Exception as e:
                                    ret[dataset]['Configure {0}'.format(remote_server)]['1'] = "Configuration failed with error: {0}".format(e)
                                    break
 
                            ret[dataset]['Configure {0}'.format(remote_server)]['0'] = "Server successfully configured for replication of {0}".format(dataset)
 
        #zettaknight_utils.parse_output(ret)
 
    return ret
 
def zfs_monitor(email_recipients, protocol=False):
 
    ret = {}
    ret[zettaknight_globs.fqdn] = {}
 
    protocol = "ssh"
 
    for dataset in zettaknight_globs.zfs_conf.iterkeys():
        if str(zettaknight_globs.zfs_conf[dataset]['secure']) == "False":
            protocol = "xinetd"
 
    monitor_cmd = "bash {0} -r \"{1}\" -p \"{2}\"".format(zettaknight_globs.zfs_monitor_script, email_recipients, protocol)
    ret[zettaknight_globs.fqdn]['Monitor ZFS System Health'] = zettaknight_utils.spawn_job(monitor_cmd)
 
    zettaknight_utils.parse_output(ret)
 
    return ret
 
 
def check_group_quota(group):
    '''
    '''
    zettaknight_globs.nocolor_flag = True
 
    ret = {}
    dset = zettaknight_utils.pipe_this2("zfs list -H -o name | grep -v {0}/ | grep {0}".format(group))
    dset = dset.stdout.read().strip()
    if dset:
        if str(group) in dset:
            usage_dict = check_usage(dset, "quiet")
    else:
        usage_dict = {}
        usage_dict[zettaknight_globs.fqdn] = {}
        usage_dict[zettaknight_globs.fqdn]['Check Group Quota'] = {1: "group: {0} does not have a Zettaknight controlled dataset.".format(group)}
 
    if str(dset) in usage_dict.iterkeys():
        if "0" in usage_dict[dset]['Check Usage'].iterkeys():
            usage_info = usage_dict[dset]['Check Usage']["0"]
            usage_info = usage_info.splitlines()
            for line in usage_info:
                if "Reservation" in line:
                    purchased = line.split(":")[1]
                    if str(purchased) == " none":
                        res = float(0.00)
                        res_unit = "G"
                    else:
                        res = float(re.sub("[A-Za-z]", "", purchased))
                        if "T" in line:
                            res_unit = "T"
                        elif "G" in line:
                            res_unit = "G"
                        elif "M" in line:
                            res_unit = "M"
 
                    #print("Purchased: {0}".format(purchased))
                if "Snapshots" in line:
                    snap_used = line.split(":")[1]
                    #print("Snapshot Data use: {0}".format(snap_used))
                if "Dataset" in line:
                    dset_used = line.split(":")[1]
                    #print("User Data use: {0}".format(dset_used))
                if "Total" in line:
                    tot_used = line.split(":")[1]
                    tot_used = float(re.sub("[A-Za-z]", "", tot_used))
                    free_size = "{0:.2f}{1}".format((res - tot_used), res_unit)
                    #print("Free Space Available: {0}".format(free_size))
 
            ret = "{0}:\t{4} available of {1} purchased. (Active User Data: {2}, Data in Snapshots: {3})".format(group, purchased, dset_used, snap_used, free_size)
 
    return ret