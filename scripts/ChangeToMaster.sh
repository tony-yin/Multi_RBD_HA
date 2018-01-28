#!/bin/bash

folder="$(dirname $1)/$(basename $1)"
fname=$(basename $folder)
if [ -d $folder ]; then
    if $(mount | grep -q "$folder "); then
        umount -f $folder > /dev/null
    fi

    device=$(rbd showmapped | awk '/image_'$fname' / {print $5}')
    if [ -b "$device" ]; then
        mount $device $folder
    fi
fi
service nfs-kernel-server restart
