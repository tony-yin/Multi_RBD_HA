class rbd_handler:
    def get_my_state(self, vip_idx):
        nodes = get_all_nodes()
        nodes.sort()

        idx = vip_idx * 2 % len(nodes)
        my_ip = get_public_ip()

        if my_ip == nodes[idx]:
            return 'MASTER'
        elif my_ip == nodes[(idx + 1) % len(nodes)]:
            return 'BACKUP'
        else:
            return None

    def get_router_id(self, vip):
        rid = 0
        for i in vip.split('/')[0].split('.'):
            rid += int(i)

        return rid

    def add_keepalived_ins(self, vip, folder, state):
        vrrp_ins = """
vrrp_instance VI_{ins_name} {{
    state {state}
    interface {pubif}
    priority {priority}
    virtual_router_id {router_id}
    advert_int 1
    authentication {{
        auth_type PASS
        auth_pass 1111
    }}
    track_script {{
        chk_nfs
    }}
    notify_master "/etc/keepalived/ChangeToMaster.sh {folder}"
    notify_backup "/etc/keepalived/ChangeToBackup.sh {folder}"
    virtual_ipaddress {{
        {vip}
    }}
}}
""".format(ins_name = vip.replace('.', '_').replace('/', '_'),
           state = state,
           priority =  200 if state == "MASTER" else 100,
           router_id = self.get_router_id(vip),
           pubif = get_public_interface(),
           folder = folder,
           vip = vip)

        return vrrp_ins

    def update_keepalived_conf(self):
        kconf = """global_defs {
    notification_email {
    }

    router_id NFS_HA_112
}

vrrp_script chk_nfs {
    script "/etc/keepalived/check_nfs.sh"
    interval 2
}
"""
        vips = self.ip_folder_map.keys()
        vips.sort()
        for vip, folder in self.ip_folder_map.items():
            vip_idx = vips.index(vip)
            state = self.get_my_state(vip_idx)
            if state is not None:
                kconf += self.add_keepalived_ins(vip, folder, state)

        with open(KEEPALIVED_CONF_PATH, 'w') as f:
            f.writelines(kconf)
        do_shell('service keepalived reload')


    def create_rbd_image(self, folder, pool_name, path):
        image = 'image_{}'.format(folder)
        if not self.is_rbd_image_exist(image, pool_name):
            do_shell('rbd create --size {} --order 19 -p {} {}'.format(RBD_IMAGE_SIZE, pool_name, image))
            block_path = do_shell('rbd map -p {} {}'.format(pool_name, image)).strip()
            do_shell('mkfs.ext4 -O ^has_journal -i 400000 {} >> /var/log/mkfs.log'.format(block_path))
            options = 'noatime,user_xattr'
            do_shell('mount -o {} {} {}'.format(options, block_path, path))
            new_size = RBD_IMAGE_SIZE + (20 * 1024 * 1024)
            do_shell('rbd resize --size {} -p {} {}'.format(new_size, pool_name, image))
            do_shell('resize2fs {} {}M'.format(block_path, new_size))

    def do_rbd_map(self, folder, pool_name, path):
        rbd_map = do_shell('rbd showmapped')
        image = 'image_{}'.format(folder)
        if self.is_rbd_image_exist(image, pool_name) and image not in rbd_map:
            do_shell('rbd map -p {} {}'.format(pool_name, image))

    def delete_rbd_image(self, folder, path):
        self.unbind_rbd_path(path)
        image= 'image_{}'.format(folder)
        rbdmap = do_shell('rbd showmapped')
        if image in rbdmap:
            result = do_shell('rbd showmapped | grep "{} "'.format(image)).split()
            if image == result[2]:
                do_shell("rbd unmap {}".format(result[4]))
                if self.is_keepalived_master(folder, True):
                    remove_image(
                        result[1],
                        image,
                        _host='localhost'
                    )


