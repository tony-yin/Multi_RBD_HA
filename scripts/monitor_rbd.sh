#!/bin/bash


function convert_to_MB()
{
    size=$1
    unit=${size:(-1):1}
    nr=${size/$unit/}
    case $unit in
        (k|K|\)) echo "$nr / 1024" | bc;;
        (m|M|\)) echo "$nr";;
        (g|G|\)) echo "$nr * 1024" | bc;;
        (t|T|\)) echo "$nr * 1024 * 1024" | bc;;
        (p|P|\)) echo "$nr * 1024 * 1024 * 1024" | bc;;
        *) echo "Error: cannot convert to MB: $size";;
    esac
}

function get_available_size()
{
    disk=$1
    unit_size=$(convert_to_MB '50T')
    
    disk_size=$(df -h | grep $disk | awk '{print $2}')
    disk_size=$(convert_to_MB $disk_size)

    pool=$(rbd showmapped | grep $disk | awk '{print $2}')
    available_pool_size=$(ceph df | grep $pool | awk '{print $5}')
    available_pool_size=$(convert_to_MB $available_pool_size)

    if [ $(echo "$available_pool_size < $unit_size" | bc) -eq 1 ]; then
        new_size=$(echo "$disk_size + $available_pool_size" | bc)
    else
        new_size=$(echo "$disk_size + $unit_size" | bc)
    fi

    echo ${new_size%.*}
}

function check_and_enlarge_disk()
{
    disk="$1"
    if [ "$disk" = "" ]; then
        echo "Error: You must specify the disk name"
        return 1
    fi

    echo "Checking the disk [/dev/$disk] ..."
    if ! rbd showmapped | grep -q $disk; then
        echo "Error: Cannot find the disk [$disk]"
        return 2
    fi

    disk_usage=$(df | grep $disk | awk '{print $5}')
    available_disk_size=$(df | grep $disk | awk '{print $4}')
    available_disk_size=$(convert_to_MB "${available_disk_size}k")
    echo "  The disk use% is ${disk_usage}"
    disk_usage=${disk_usage/\%/}
    if [ $disk_usage -lt 50 -a $available_disk_size -gt 1024 * 1024 * 50 ]; then
        echo 'Less then 50% use and more then 50TB available space left, just quit'
        return 0
    fi

    echo 'Enlarging the disk ...'
    new_size=$(get_available_size $disk)
    echo "  the new size is ${new_size}MB"

    pool=$(rbd showmapped | grep $disk | awk '{print $2}')
    image=$(rbd showmapped | grep $disk | awk '{print $3}')

    rbd resize --size $new_size -p $pool $image
    sleep 3
    resize2fs /dev/${disk} "${new_size}M"
    echo "Done"
}

disks=$(lsblk | grep rbd | awk '{print $1}')
for disk in $disks
do
echo "=============================================="
check_and_enlarge_disk "$disk"
echo "=============================================="
done
