#!/bin/bash

folder=$1
service nfs-kernel-server stop
if [ -d $folder ]; then
    if $(mount | grep -q "$folder "); then
        umount -f $folder > /dev/null
    fi
fi
service nfs-kernel-server start
