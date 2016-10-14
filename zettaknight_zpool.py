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
import zettaknight_zfs
import sys


def create(*args, **kwargs):

    if zettaknight_globs.help_flag:
        ret = """Create Zpool:

	Usage:
		zettaknight create <optional args>
	
    Creates a Zpool using information in zettaknight zpool.conf or overrides provided as arguments.

    Optional Arguments:
        positional arguments:
			pool
				Name of zpool to be created.
		
		k=v pairs:
			disk_list
				File containing full path of disk devices to be used in pool creation.
			raid
				Raid configuration to be used in pool creation in the form of <data disks+<raid type>, ie 9+2, or 4+1.
					acceptable raid type values and corresponding raid type:
						0. Stripe
						1. Raidz1
						2. Raidz2
						3. Raidz3
						4. Mirror
			luks
				True or False.  Whether or not to create luks devices out of disks provided in disk_list.
			slog
				File containing full path of disk devices to be used in creation of a slog.
			ashift
				Ashift value to be passed to zpool create command.
			ldap
				True or False.  Whether or not to set the following pool properties:
					xattr = sa
					acltype = posixacl
					aclinherit = passthrough
			recordsize
				Recordsize value to be passed to zpool create command.
			keyfile
				Location of keyfile to be used in creation of luks containers.  By default, the Zettaknight keyfile will be used.  Specifying another keyfile will overwrite this behavior.
			
			"""
        return ret

    disk_list = bool(False)
    raid = bool(False)
    luks = bool(False)
    slog = bool(False)
    arg_list = list(args)
    pool = str(zettaknight_globs.pool_name)
    create_config = bool(False)
    ldap_flag = bool(True)
    recordsize = bool(False)
    ashift = bool(False)
    keyfile = bool(False)
    
    ret = {}
    ret[pool] = {}
    ret[pool]['Create Zpool'] = {}


    if len(arg_list) > 1:
        print("Unexpected arguments found.  Could not parse: {0}\n All arguments other than pool_name should be in key=value pairs.".format(arg_list))
        sys.exit(0)
    
    if arg_list:
        pool = arg_list[0]
    if kwargs:
        if 'disk_list' in kwargs.iterkeys():
            disk_list = kwargs['disk_list']
        if 'raid' in kwargs.iterkeys():
            raid = kwargs['raid']
        if 'luks' in kwargs.iterkeys():
            luks = kwargs['luks']
            if 'keyfile' in kwargs.iterkeys():
                keyfile = kwargs['keyfile']
            else:
                keyfile = zettaknight_globs.identity_file
        if 'slog' in kwargs.iterkeys():
            slog = kwargs['slog']
        if 'create_config' in kwargs.iterkeys():
            create_config = kwargs['create_config']
        if 'ldap' in kwargs.iterkeys():
            ldap_flag = kwargs['ldap']
        if 'recordsize' in kwargs.iterkeys():
            recordsize = kwargs['recordsize']
        if 'ashift' in kwargs.iterkeys():
            ashift = kwargs['ashift']


    create_cmd = create_zpool(pool, disk_list, raid, luks, slog, create_config, ldap_flag, recordsize, ashift, keyfile) 
    ret[pool]['Create Zpool'] = create_cmd[pool]['Create Zpool']

    return ret


def create_zpool(pool=False, disk_list=False, raid=False, luks=False, slog=False, create_config=False, ldap=False, recordsize=False, ashift=False, keyfile=False):

    if zettaknight_globs.help_flag:
        ret = """Create Zpool:

		See help entry for create function.
		
		zettaknight help create
		"""
        return ret

    ret = {}

    ret[pool] = {}
    ret[pool]['Create Zpool'] = {}

    if not raid:
        raid = "12+2"
    try:
        disks, z_level = raid.split("+")
    except Exception as e:
        ret[pool]['Create Zpool'] = {'1': "{0}\nargument raid must be in x+y format, i.e. 2+1".format(e)}
        zettaknight_utils.parse_output(ret)
        sys.exit(0)

    create_cmd = "bash {0} -d {1} -z {2}".format(zettaknight_globs.zpool_create_script, disks, z_level)

    if disk_list:
        create_cmd = "{0} -f '{1}'".format(create_cmd, disk_list)

    if pool:
        create_cmd = "{0} -p '{1}'".format(create_cmd, pool)

    if luks:
        create_cmd = "{0} -l".format(create_cmd)

    if slog:
        create_cmd = "{0} -s '{1}'".format(create_cmd, slog)
        
    if ldap:
        create_cmd = "{0} -i".format(create_cmd)
        
    if recordsize:
        if any(i in recordsize for i in 'KM'):
            create_cmd = "{0} -r {1}".format(create_cmd, recordsize)
        else:
            print(zettaknight_utils.printcolors("Recordsize must be in number/unit format.  ie. 1M, or 512K", "FAIL"))
            sys.exit(0)
            
    if ashift:
        create_cmd = "{0} -a {1}".format(create_cmd, ashift)
    if keyfile:
        create_cmd = "{0} -k {1}".format(create_cmd, keyfile)

    try:
        ret[pool]['Create Zpool'] = zettaknight_utils.spawn_job(create_cmd)
    except Exception as e:
        zettaknight_utils.zlog("{0}".format(e), "ERROR")
        ret[pool]['Create Zpool']['1'] = e
        
    return ret
