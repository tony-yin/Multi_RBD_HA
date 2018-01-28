def update_ip_folder_map_by_folder(folder, type):
    ip_folder_map = vip.get_ip_folder_map()
    folder = get_folder_path(folder)
    if type == "add":
        for k, v in ip_folder_map.iteritems():
            if k == v:
                ip_folder_map[k] = folder
                break
    elif type == "delete":
        for k,v in ip_folder_map.iteritems():
            if v == folder:
                ip_folder_map[k] = k
                break

    vip.set_ip_folder_map(ip_folder_map)


