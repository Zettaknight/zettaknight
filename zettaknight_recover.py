#!/usr/bin/python
# -*- coding: utf-8 -*-
# Import python libs

import zettaknight_utils
import zettaknight_globs
import os
import subprocess
import shlex
import inspect
import datetime
import re


def find_versions(dataset, filename, quiet=False):
    '''
    '''
    zettaknight_utils.check_quiet(quiet)
    
    snaps = {}
    ret = {}
    ret[dataset] = {}
    snaplist_cmd = "/sbin/zfs list -r -t snapshot -o name -H {0}".format(dataset)
    snaplist_run = subprocess.Popen(shlex.split(snaplist_cmd), stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
    snaplist_run.wait()
    snaplist_out = snaplist_run.stdout.read()
    if not snaplist_out:
        try:
            out_dict = {}
            out_dict[dataset] = {}
            job = inspect.stack()[0][3]
            if str(inspect.stack()[1][3]) is 'recover':
                job = inspect.stack()[1][3]
                
            out_dict[dataset][job] = {}
            out_dict[dataset][job]['1'] = "No snapshots found."
            raise Exception
        except Exception as e:
            zettaknight_utils.parse_output(out_dict)
            sys.exit(0)
    
    for snap in snaplist_out.split():
        if snap.startswith("cannot"):
            try:
                raise Exception("{0}".format(snaplist_out))
            except Exception as e:
                print(zettaknight_utils.printcolors(e, "FAIL"))
                sys.exit(0)
                
        snapdiff_cmd = "/sbin/zfs diff {0}".format(snap)
        gerp_cmd = "/bin/grep {0}".format(filename)
        gerp_run = zettaknight_utils.pipe_this(snapdiff_cmd, gerp_cmd)

        gerp_out = gerp_run.stdout.read()
        gerp_list = []

        if gerp_out:
            for gerp in gerp_out.split('\n'):
                if gerp.startswith("-") or gerp.startswith("M"):
                    gerp_list.append(gerp)

            if gerp_list:
                snaps[snap] = gerp_list
                gerp_msg = ""
                for z in gerp_list:
                    if gerp_msg:
                        gerp_msg = "{0}\n{1}".format(gerp_msg, z)
                    else:
                        gerp_msg = str(z)
                        
                    job = "Snapshot: {0}".format(snap)
                    ret[dataset][job] = {}
                    
                    job_out = "Path:\n{0}".format(gerp_msg)
                    ret[dataset][job]['0'] = job_out
                    
    if not ret[dataset]:
        ret[dataset]['Snapshot'] = {}
        ret[dataset]['Snapshot']['1'] = "No modified versions of {0} found.".format(filename, dataset)
        
    if not quiet:
        zettaknight_utils.parse_output(ret)
                       
    return snaps
    
    
def recover(snapshot, filename, relocate=None):
    '''
    '''
    
    file = filename
    snap = snapshot
    dataset, snap_date = snap.split('@', 1)
    find_snap = find_versions(dataset, file, "quiet")
    find_snap_keys = find_snap.iterkeys()
    snap_basedir = "/{0}/.zfs/snapshot".format(dataset)
    active_basedir = "/{0}".format(dataset)
    dir_flag = False
    ret = {}
    ret[dataset] = {}
    
    
    if dataset in file.split("/"):
        file = file.split(dataset, 1)[1]
        last_ref = file.rsplit("/",1)[1]
    
    if snap not in find_snap_keys:
        try:
            raise Exception("Recoverable versions of {0} not found in dataset {1}".format(file, dataset))
        except Exception as e:
            print(zettaknight_utils.printcolors(e, "FAIL"))
    
    path_list1 = find_snap[snap]
    
    path_list = []
    
    if os.path.isdir("/{0}/{1}".format(dataset, file)):
        dir_flag = True
    
    for line in path_list1:
        if line.startswith("-") or line.startswith("M"):
            a, b = line.rsplit("/", 1)
            if not dir_flag:
                try:
                    if str(b) == str(last_ref):
                        path_list.append(line)
                except:
                    if str(b) == str(file):
                        path_list.append(line)
                    pass
                        

            else:
                if a.startswith("-"):
                    a, b = line.rsplit(dataset, 2)
                    if os.path.isdir("{0}/{1}{2}".format(snap_basedir, snap_date, b)):
                        dir_flag = True
                        path_list.append(line)

    if len(path_list) > 1:
        exc_out = ""
        for i in path_list:
            if exc_out:
                exc_out = "{0}\n\t{1}".format(exc_out, i)
            else:
                exc_out = str(i)
        err_msg = "Matching files/folders in snapshot:"
        print(zettaknight_utils.printcolors("\nAmbiguous recover request.  Multiple matches for {0}.".format(file), "FAIL"))
        print("{0} {1}".format(zettaknight_utils.printcolors(err_msg, "FAIL"), zettaknight_utils.printcolors(snap, "OKBLUE")))
        print("\t{0}".format(zettaknight_utils.printcolors(exc_out, "WARNING")))
        print(zettaknight_utils.printcolors("Re-run with explicit path to file.\n", "FAIL"))
        try:
            raise Exception("Ambiguous file reference.")
        except Exception as e:
            print(zettaknight_utils.printcolors(e, "FAIL"))
            sys.exit(0)
    
    if len(path_list) < 1:
        try:
            raise Exception("No restorable files or folders identified. \nRe-run with explicit path to file?")
        except Exception as e:
            print(zettaknight_utils.printcolors(e, "FAIL"))
            sys.exit(0)
    
    a, p = path_list[0].split(dataset, 1)
    path, dirs = p.split(file, 1)

    if dir_flag:
        bad, dir_path = path_list[0].split(file, 1)
        list_dirs = dir_path.rsplit("/", 1)
        try:
            out_dir = list_dirs[0]
        except:
            out_dir = ""
            pass
        
        file_loc = "{0}/{1}/{2}{3}/".format(snap_basedir, snap_date, file, dir_path )
        mkdir_cmd = "/bin/mkdir {0}/{1}.R".format(active_basedir, file)
        mkdir_run = zettaknight_utils.spawn_job(mkdir_cmd)
        mkdir_cmd = "/bin/mkdir -p {0}/{1}.R/{2}".format(active_basedir, file, dir_path)
        mkdir_run = zettaknight_utils.spawn_job(mkdir_cmd)
        out_path = "{0}{1}{2}.R{3}/".format(active_basedir, str(path), file, out_dir)

    else:
        file_loc = "{0}/{1}/{2}".format(snap_basedir, snap_date, p)
        out_path = "{0}{1}{2}.R".format(active_basedir, str(path), file)

    if relocate:
        out_path = relocate
    
    rec_cmd = "/bin/cp ""-r ""{0}"" ""{1}".format(file_loc, out_path)
    rec_run = zettaknight_utils.spawn_job(rec_cmd)
    rec_dict = eval(str(rec_run))
    for k,v in rec_dict.iteritems():
        if str(k) is "0":
            print("Recover operation succeeded.")
            print("\tFilename: {0}".format(zettaknight_utils.printcolors(file, "OKBLUE")))
            print("\t\tFile(s) restored to version: {0}".format(zettaknight_utils.printcolors(snap_date, "OKGREEN")))
            print("\t\tFile(s) restored to: {0}".format(zettaknight_utils.printcolors(out_path, "OKGREEN")))

        if str(k) is not "0":
            print("Recover operation failed.")
            print("\tFilename: {0}".format(zettaknight_utils.printcolors(file, "OKBLUE")))
            print("\t\tRestore failed with error: {0}".format(zettaknight_utils.printcolors(v, "FAIL")))
    
    return
