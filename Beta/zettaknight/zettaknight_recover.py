#!/usr/bin/python
# -*- coding: utf-8 -*-
#
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

import zettaknight_utils
import zettaknight_globs
import sys
import os
import subprocess
import shlex
import inspect
import datetime
import re


def find_versions(dataset, filename, quiet=False):
    '''
    '''
	
    if zettaknight_globs.help_flag:
        ret = """Find Versions:

	Usage:
		zettaknight find_versions zfs_data/<some dataset> <some filename>
	
    Searches snapshots of provided dataset for previous versions of filename.

    Required Arguments:
        dataset
            Specifies the dataset whose snapshots will be searched.
		filename
			Defines target file(s) to find previous versions of.  This can be a full path to a file (/zfs_data/<some dataset>/<some filename>.<ext>), just a filename with or without an extension (<some filename> or <some filename>.<ext>), or just an extension (.<ext>)"""
        return ret
		
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
                zettaknight_utils.zlog("{0}".format(e), "ERROR")
                sys.exit(0)
                
        snapdiff_cmd = "/sbin/zfs diff {0}".format(snap)
        gerp_cmd = "/bin/grep {0}".format(filename)
        gerp_run = zettaknight_utils.pipe_this(snapdiff_cmd, gerp_cmd)

        gerp_out = gerp_run.stdout.read()
        gerp_list = []

        if gerp_out:
            for gerp in gerp_out.split('\n'):
                if gerp.startswith("-") or gerp.startswith("M") or gerp.startswith("R"):
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
    if zettaknight_globs.help_flag:
        ret = """Recover:

	Usage:
		zettaknight recover <snapshot> <filepath> (<directory to recover file to>)*optional
	
    Recovers a previous version of a file or folder from a specified snapshot.  Information to use in calling zettaknight recover can be found in the output from the find_versions function.  By default, files/folders will be recovered to their original location with .R appended to the end of the name.

    Required Arguments:
        snapshot
            Specifies the snapshot to recover files from.
		filename
			Defines target file(s) to recover.  This should be the full path to a file or folder (/zfs_data/<some dataset>/<some filename>.<ext>)
			
	Optional Arguments:
		relocate
			Defines an alternate path to recover files/folders to.  If used, .R will not be appended, and the recover will overwrite any existing files."""
        return ret
		
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
    
  
    try:
        if str(dataset) in str(file):
            file = file.split(dataset, 1)[1]
            last_ref = file.rsplit("/", 1)[1]
    except Exception as e:
        pass

    if dataset in file.rsplit("/", 1):
        file = file.split(dataset, 1)[1]
        last_ref = file.rsplit("/",1)[1]

    if snap not in find_snap_keys:
        try:
            raise Exception("Recoverable versions of {0} not found in dataset {1}".format(file, dataset))
        except Exception as e:
            zettaknight_utils.zlog("{0}".format(e), "ERROR")
    
    path_list1 = find_snap[snap]
    
    path_list = []
    
    if os.path.isdir("/{0}{1}".format(dataset, file)):
        dir_flag = True

    for line in path_list1:
        if line.startswith("-") or line.startswith("M") or line.startswith("R"):
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
                if a.startswith("-") or line.startswith("M") or line.startswith("R"):
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
            zettaknight_utils.zlog("{0}".format(e), "ERROR")
            sys.exit(0)
    
    if len(path_list) < 1:
        try:
            raise Exception("No restorable files or folders identified. \nRe-run with explicit path to file?")
        except Exception as e:
            zettaknight_utils.zlog("{0}".format(e), "ERROR")
            sys.exit(0)
    
    a, p = path_list[0].split(dataset, 1)
    path, dirs = p.split(file, 1)

    if dir_flag:
        a, b = path_list[0].rsplit(dataset, 2)
        file_loc = "{0}/{1}{2}".format(snap_basedir, snap_date, b)
        #bad, dir_path = path_list[0].split(file, 1)
        #list_dirs = dir_path.rsplit("/", 1)
        #try:
        #    out_dir = list_dirs[0]
        #except:
        out_dir = ""
        #    pass
        
        #file_loc = "{0}/{1}/{2}{3}/".format(snap_basedir, snap_date, file, dir_path )
        #mkdir_cmd = "/bin/mkdir {0}/{1}.R".format(active_basedir, file)
        #mkdir_run = zettaknight_utils.spawn_job(mkdir_cmd)
        #mkdir_cmd = "/bin/mkdir -p {0}/{1}.R/{2}".format(active_basedir, file, dir_path)
        #mkdir_run = zettaknight_utils.spawn_job(mkdir_cmd)
        out_path = "{0}{1}{2}.R{3}/".format(active_basedir, str(path), file, out_dir)

    else:
        file_loc = "{0}/{1}/{2}".format(snap_basedir, snap_date, p)
        out_path = "{0}{1}{2}.R".format(active_basedir, str(path), file)

    if relocate:
        out_path = relocate
    
    rec_cmd = "/bin/cp ""-r -p ""{0}"" ""{1}".format(file_loc, out_path)
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

def audit_last_snap(dataset):
    '''
    '''
    
    if zettaknight_globs.help_flag:
        ret = """Last Snapshot Audit:

	Usage:
		zettaknight audit_last_snap <dataset>
	
    Returns an audit of all differences between the two most recent snapshots of a dataset.

    Required Arguments:
        dataset
            Specifies the dataset whose snapshots will be audited."""
        return ret
		
    snaps = {}
    ret = {}
    ret[dataset] = {}
    job = inspect.stack()[0][3]
    snaplist_run = zettaknight_utils.pipe_this2("/sbin/zfs list -r -t snapshot -o name -H {0} | tail -2".format(dataset))
    snaplist_out = snaplist_run.stdout.read()
    if not snaplist_out:
        try:
            ret[dataset][job] = {}
            ret[dataset][job]['1'] = "No snapshots found."
            raise Exception
        except Exception as e:
            return ret
    
    snap_list = list(snaplist_out.split())
    if snap_list[0].startswith("cannot"):
        try:
            ret[dataset][job] = {}
            ret[dataset][job]['1'] = "{0}".format(snap_list[0])
            raise Exception
        except Exception as e:
            return ret
                
    if len(snap_list) == 2:
        diff_cmd = "/sbin/zfs diff {0} {1} -H | cat".format(snap_list[0], snap_list[1])
        job = "Audit of newly ingested snapshot {0}".format(snap_list[1])
    else:
        diff_cmd = "/sbin/zfs diff {0} -H | cat".format(snap_list[0])
        job = "Audit of newly ingested snapshot {0}".format(snap_list[0])
        
    diff_run = zettaknight_utils.pipe_this2("{0}".format(diff_cmd))
    diff_out = diff_run.stdout.read()
        
    if diff_out:
        mod_count = 0
        mod_list = ""
        add_count = 0
        add_list = ""
        del_count = 0
        del_list = ""
        for diff in diff_out.split('\n'):
            if diff.startswith("M"):
                mod_count += 1
                if mod_list:
                    mod_list = "{0}\n\t{1}".format(mod_list, diff)
                else:
                    mod_list = "\t{0}".format(str(diff))
            
            if diff.startswith("+"):
                add_count += 1
                if add_list:
                    add_list = "{0}\n\t{1}".format(add_list, diff)
                else:
                    add_list = "\t{0}".format(str(diff))
                    
            if diff.startswith("-"):
                del_count += 1
                if del_list:
                    del_list = "{0}\n\t{1}".format(del_list, diff)
                else:
                    del_list = "\t{0}".format(str(diff))
        
    ret[dataset][job] = {}
    job_out = ""

    if mod_list:
        job_out = "\nFile modifications in last ingested snapshot:\n{0}".format(mod_list)
    if add_list:
        job_out = "{0}\n\nNew Files in last ingested snapshot:\n{1}".format(job_out, add_list)
    if del_list:
        job_out = "{0}\n\nFile deletions in last ingested snapshot:\n{1}".format(job_out, del_list)
    
    job_out = "{0}\n\nChange counts in last ingested snapshot:\n\tModified Files: {1}\n\tNew Files: {2}\n\tDeleted Files: {3}".format(job_out, str(mod_count), str(add_count), str(del_count))
    
    ret[dataset][job]['0'] = job_out
    
    return ret
