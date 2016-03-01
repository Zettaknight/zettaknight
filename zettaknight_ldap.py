#!/usr/bin/python
# -*- coding: utf-8 -*-
# Import python libs
 
import inspect
import re
import sys
  
#from zettaknight import *
import zettaknight_utils
import zettaknight_globs
import paramiko


def create_cifs_share(**kwargs):
    '''
    Creates a zfs dataset for a given user or group.    
    '''
    ret = {}
    
    user = False
    group = False
    
    if kwargs:
        try:
            if kwargs['dataset']:
                dataset = kwargs['dataset']
        except:
            dataset = "{0}/{1}".format(zettaknight_globs.pool_name, zettaknight_globs.cifs_dset_suffix)
            pass
    
    if kwargs and "user" in kwargs.iterkeys():
        user = kwargs['user']
        
    if kwargs and "group" in kwargs.iterkeys():
        group = kwargs['group']
    
    ret[dataset] = {}
    
    if user and group:
        try:
            raise Exception("Arguments user and group must be specified separately.  Arguments passed: {0}".format(kwargs))
        except Exception as e:
            ret[dataset]['Create CIFS Share'] = {1: e}
            zettaknight_utils.parse_output(ret)
            return ret
        
    if user:
        cifs_cmd = "{0} -u {1} -d {2}".format(zettaknight_globs.cifs_share_script, user, dataset)
    
    if group:
        cifs_cmd = "{0} -g {1} -d {2}".format(zettaknight_globs.cifs_share_script, group, dataset)
    
    if user:
        obj = user
    elif group:
        obj = group

    try:
        if str(zettaknight_globs.zfs_conf[dataset]['primary']) == str(zettaknight_globs.fqdn):
            if zettaknight_globs.zfs_conf[dataset]['snap']['remote_server']:
                for remote_server in zettaknight_globs.zfs_conf[dataset]['snap']['remote_server']:
                    remote_user = zettaknight_globs.zfs_conf[dataset]['user']
                    remote_ssh = "{0}@{1}".format(remote_user, remote_server)
                    try:
                        ssh2 = paramiko.SSHClient()
                        ssh2.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                        ssh2.connect(remote_server, username=remote_user, key_filename=zettaknight_globs.identity_file)
                        remote_cmd = "zettaknight create_cifs_share user={0} dataset={1}".format(obj, dataset)
                        ssh2_stdin, ssh2_stdout, ssh2_stderr = ssh2.exec_command(remote_cmd)
                        ssh2.close()
                    except Exception as e:
                        pass
    except:
        pass

    try:
        ret[dataset]['Create CIFS Share'] = zettaknight_utils.spawn_job(cifs_cmd)
    except Exception as e:  
        ret[dataset]['Create CIFS Share'] = {1: e}
    
    #zettaknight_utils.parse_output(ret)
    
    return ret
  
def set_cifs_quota(**kwargs):
    '''
    Set quota for user or group cifs share.
    '''
    
    ret = {}
    user = False
    group = False
    quota = False
    
    try:
        if kwargs and kwargs['dataset']:
            dataset = kwargs['dataset']
    except:
        dataset = "{0}/{1}".format(zettaknight_globs.pool_name, zettaknight_globs.cifs_dset_suffix)
        pass
    
    if kwargs and "user" in kwargs.iterkeys():
        user = kwargs['user']
        
    if kwargs and "group" in kwargs.iterkeys():
        group = kwargs['group']
    
    if kwargs and "quota" in kwargs.iterkeys():
        quota = kwargs['quota']
    
    
    if user and group:
        ret[dataset] = {}
        try:
            raise Exception("Arguments user and group must be specified separately.  Arguments passed: {0}".format(kwargs))
        except Exception as e:
            ret[dataset]['Set User Quota'] = {1: e}
            zettaknight_utils.parse_output(ret)
            return ret

    if not quota:
        ret[dataset] = {}
        try:
            raise Exception("Quota argument must be supplied.  Arguments passed: {0}".format(kwargs))
        except Exception as e:
            ret[dataset]['Set User Quota'] = {1: e}
            zettaknight_utils.parse_output(ret)
            return ret

    if user:
        obj = user
        dset = "{0}/{1}".format(dataset, user)
    elif group:
        obj = group
        dset = "{0}/{1}".format(dataset, group)
    
    try:
        if str(zettaknight_globs.zfs_conf[dataset]['primary']) == str(zettaknight_globs.fqdn):
            if zettaknight_globs.zfs_conf[dataset]['snap']['remote_server']:
                for remote_server in zettaknight_globs.zfs_conf[dataset]['snap']['remote_server']:
                    remote_user = zettaknight_globs.zfs_conf[dataset]['user']
                    remote_ssh = "{0}@{1}".format(remote_user, remote_server)
                    try:
                        ssh2 = paramiko.SSHClient()
                        ssh2.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                        ssh2.connect(remote_server, username=remote_user, key_filename=zettaknight_globs.identity_file)
                        remote_cmd = "zettaknight set_cifs_quota user={0} dataset={1} quota={2}".format(obj, dataset, quota)
                        ssh2_stdin, ssh2_stdout, ssh2_stderr = ssh2.exec_command(remote_cmd)
                        ssh2.close()
                    except Exception as e:
                        pass
    except:
        pass
		
    ret[dset] = {}
    
    quota_cmd = "/sbin/zfs set quota={0} {1}".format(quota, dset)
    ret[dset]['Set User Quota'] = zettaknight_utils.spawn_job(quota_cmd)
    
    return ret
	
	
def get_cifs_quota(**kwargs):
    '''
    get quota for user or group cifs share.
    '''
    
    ret = {}
    user = False
    group = False
        
    try:
        if kwargs and kwargs['dataset']:
            dataset = kwargs['dataset']
    except:
        dataset = "{0}/{1}".format(zettaknight_globs.pool_name, zettaknight_globs.cifs_dset_suffix)
        pass
    
    if kwargs and "user" in kwargs.iterkeys():
        user = kwargs['user']
        
    if kwargs and "group" in kwargs.iterkeys():
        group = kwargs['group']
  
    
    if user and group:
        ret[dataset] = {}
        try:
            raise Exception("Arguments user and group must be specified separately.  Arguments passed: {0}".format(kwargs))
        except Exception as e:
            ret[dataset]['Get User Quota'] = {1: e}
            zettaknight_utils.parse_output(ret)
            return ret

    if user:
        dset = "{0}/{1}".format(dataset, user)
    elif group:
        dset = "{0}/{1}".format(dataset, group)  
    
    ret[dset] = {}
    quota_cmd = "/sbin/zfs get quota -H {0} -o value".format(dset)
    ret[dset]['Get User Quota'] = zettaknight_utils.spawn_job(quota_cmd)
    
    return ret


def get_cifs_share(**kwargs):
    '''
    get quota for user or group cifs share.
    '''
    
    ret = {}
    user = False
    group = False
        
    try:
        if kwargs and kwargs['dataset']:
            dataset = kwargs['dataset']
    except:
        dataset = "{0}/{1}".format(zettaknight_globs.pool_name, zettaknight_globs.cifs_dset_suffix)
        pass
    
    if kwargs and "user" in kwargs.iterkeys():
        user = kwargs['user']
        
    if kwargs and "group" in kwargs.iterkeys():
        group = kwargs['group']
  
    
    if user and group:
        ret[dataset] = {}
        try:
            raise Exception("Arguments user and group must be specified separately.  Arguments passed: {0}".format(kwargs))
        except Exception as e:
            ret[dataset]['Get User Quota'] = {1: e}
            zettaknight_utils.parse_output(ret)
            return ret

    if user:
        dset = "{0}/{1}".format(dataset, user)
    elif group:
        dset = "{0}/{1}".format(dataset, group)  
    
    ret[dset] = {}
    quota_cmd = "/sbin/zfs list -H {0} -o name".format(dset)
    #ret[dset]['Get User Share'] = zettaknight_utils.spawn_job(quota_cmd)
    job_out = zettaknight_utils.spawn_job(quota_cmd)
    print("JOB OUT: {0}".format(job_out))
    
    if 0 in job_out.iterkeys():
        job_out[0] = "//{0}/{1}/{2}".format(str(zettaknight_globs.samba_service_name), str(zettaknight_globs.samba_share_suffix), str(user)) 
        print("JOB OUT: {0}".format(job_out))
        
    ret[dset]['Get User Share'] = job_out    

    return ret
