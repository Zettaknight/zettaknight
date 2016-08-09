#!/bin/bash

#reinstall zfs

set -e

echo -e "\nremoving zfs"
yum remove zfs -y 

echo -e "\nremoving broken kernel objects"
for i in $(ls /lib/modules); do 
    echo $i
    
    ls /lib/modules/${i}/extra 
    rm -rf /lib/modules/${i}/extra/*
    
    ls /lib/modules/${i}/weak-updates
    rm -rf /lib/modules/${i}/weak-updates/*

done


yum reinstall spl spl-dkms -y 
yum reinstall zfs-dkms -y 
yum install zfs -y

