#!/usr/bin/python
import os
import time
import rados
import rbd
from vip import get_ip_folder_map
import do_shell

CEPH_CONF = '/etc/ceph/ceph.conf'
MAX_SNAP_COUNT = 5

def create_snap(pool, rbd_image):
    now = time.localtime()
    snap = time.strftime("%Y_%m_%d_%H_%M_%S", now)

    with rados.Rados(conffile=CEPH_CONF) as cluster:
        with cluster.open_ioctx(str(pool)) as ioctx:
            with rbd.Image(ioctx, rbd_image) as image:
                image.create_snap(snap)

def get_images():
    pubif = get_public_interface()
    pub_ips = do_cmd("ip addr show {} | awk '/inet/ {{print $2}}'".format(pubif)).split()
    vip_folders = get_ip_folder_map()

    my_folders = []
    for pip in pub_ips:
        if pip in vip_folders and pip != vip_folders[pip]:
            my_folders.append(os.path.basename(vip_folders[pip]))

    folders = get_all_folder_info()
    images = []
    for folder in folders:
        if folder in my_folders:
            images.append({
                'image': 'image_{}'.format(folder),
                'pool': folders[folder]['pool']
            })

    return images

def remove_old_snap(pool, rbd_image):
    with rados.Rados(conffile=CEPH_CONF) as cluster:
        with cluster.open_ioctx(str(pool)) as ioctx:
            with rbd.Image(ioctx, rbd_image) as image:
                snaps = sorted(image.list_snaps(), key=lambda snap: snap['name'])
                if len(snaps) > MAX_SNAP_COUNT:
                    for snap in snaps[0:len(snaps)-MAX_SNAP_COUNT]:
                        image.remove_snap(snap['name'])

def main():
    images = get_images()
    for image in images:
        create_snap(image['pool'], image['image'])
        remove_old_snap(image['pool'], image['image'])
        device = do_cmd("rbd showmapped | awk '/{}[ \t]*{}/ {{print $5}}'".format(image['pool'], image['image']))
        do_cmd('/usr/local/bin/monitor_rbd.sh {}'.format(os.path.basename(device)))

if __name__ == "__main__":
    main()
