#!/usr/bin/python
# -*- coding: utf-8 -*-
# Import python libs
 
import inspect
import re
import sys
  
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
    zettaknight_utils.parse_output(ret)
      
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
  
  
def take_snap(dataset, user, remote_server, secure, nosnap=False):
    '''
    '''
      
    snap_cmd = "bash {0} -d {1} -i {2} -s {3}@{4}".format(zettaknight_globs.snap_script, dataset, zettaknight_globs.identity_file, user, remote_server)
    if secure:
        snap_cmd = "{0} -e".format(snap_cmd)
         
    if nosnap:
        snap_cmd = "{0} -r".format(snap_cmd)
  
    ret = zettaknight_utils.spawn_job(snap_cmd)
  
    return ret
  
  
  
def create_snap(dataset, quiet=False):
    '''
    '''
      
    zettaknight_utils.check_quiet(quiet)
                  
    today_date = str(datetime.datetime.today().strftime('%Y%m%d_%H%M'))
    snap = "{0}@{1}".format(dataset, today_date) 
      
    snaplist_cmd = "/sbin/zfs list -r -t snapshot -o name -H {0}".format(dataset)
    gerp_cmd = "/bin/grep {0}".format(snap)
    gerp_run = zettaknight_utils.pipe_this(snaplist_cmd, gerp_cmd)
  
    gerp_out = gerp_run.stdout.read()
      
    if int(gerp_run.returncode) is not 0:
        ret = zettaknight_utils.spawn_job("/sbin/zfs snapshot -r {0}".format(snap))
  
    if int(gerp_run.returncode) == 0:
        ret = {1: "Snapshot {0} already exists.".format(snap)}
  
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
    ret = zettaknight_utils.spawn_job(quota_cmd)
      
    return ret
      
  
def set_reservation(dataset, reservation, quiet=False):
    '''
    '''
      
    zettaknight_utils.check_quiet(quiet)
      
    #reservation_cmd = "bash {0} -d {1} -r {2}".format(zettaknight_globs.quota_script,dataset,reservation)
    reservation_cmd = "/sbin/zfs set reservation={0} {1}".format(reservation, dataset)
    ret = zettaknight_utils.spawn_job(reservation_cmd)
      
    return ret
  
  
def cleanup_snaps(dataset, retention):
    '''
    '''
      
    cleanup_cmd = "bash {0} -d {1} -k {2}".format(zettaknight_globs.cleanup_script, dataset, retention)
    ret = zettaknight_utils.spawn_job(cleanup_cmd)
      
    return ret
  
  
def check_usage():
    '''
    '''
      
    ret = {}
    for dataset in zettaknight_globs.zfs_conf.iterkeys():
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
            avail = float(re.sub("[A-Za-z]", "", chk_msg_split[1]))
            used = float(re.sub("[A-Za-z]", "", chk_msg_split[2]))
            usnap = float(re.sub("[A-Za-z]", "", chk_msg_split[3]))
            uds = float(re.sub("[A-Za-z]", "", chk_msg_split[4]))
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
                      
    zettaknight_utils.parse_output(ret)
          
    return ret
  
  
def add_dataset(*args, **kwargs):
    '''if create_config=True is passed, a configuration file
    will be created for the datset passed in to this function'''
      
      
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
      
      
    test_if_dataset = "zfs list {0}".format(dataset)
    gerp_cmd = "/bin/grep {0}".format(dataset)
    gerp_run = zettaknight_utils.pipe_this(test_if_dataset, gerp_cmd)
    gerp_out = gerp_run.stdout.read()
      
    try:
        if kwargs['create_config']:
            print(zettaknight_utils.printcolors("\nWill create {0} after completion of config file\n".format(dataset), "OKGREEN"))
            print(zettaknight_utils.printcolors("creating config file for {0}".format(arg_list),"WARNING"))
            conf_dict = {'dataset' : dataset}
            zettaknight_utils.create_config(**conf_dict)
    except Exception as e:
        print(zettaknight_utils.printcolors(e, "FAIL"))
        sys.exit(1)
      
      
    #create dataset after commit of file
    if int(gerp_run.returncode) is not 0:
        create_cmd = "zfs create -p {0}".format(dataset)
        create_run = zettaknight_utils.spawn_job(create_cmd)
        ret[dataset]['add_dataset'] = create_run
    else:
        ret[dataset]['add_dataset'] = {'0' : "{0} exists".format(dataset)}
  
    zettaknight_utils.parse_output(ret)
  
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
                                  
        zettaknight_utils.parse_output(ret)
          
    return ret
     
def zfs_monitor(email_recipients, protocol=False):
     
    ret = {}
    ret[zettaknight_globs.fqdn] = {}
     
    protocol = "ssh"   
     
    for dataset in zettaknight_globs.zfs_conf.iterkeys():
        if str(zettaknight_globs.zfs_conf[dataset]['secure']) == "False":
            protocol = "xinetd"
         
    monitor_cmd = "bash {0} --recipient \"{1}\" --protocol \"{2}\"".format(zettaknight_globs.zfs_monitor_script, email_recipients, protocol)
    ret[zettaknight_globs.fqdn]['Monitor ZFS System Health'] = zettaknight_utils.spawn_job(monitor_cmd)
     
    zettaknight_utils.parse_output(ret)
     
    return ret
