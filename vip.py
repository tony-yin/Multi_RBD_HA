def get_ip_folder_map():
    result = {}
    ip_folder_map = LevelDB("ip_folder_map")
    result = json.loads(ip_folder_map)["ip_folder_map"]

    return result

def set_ip_folder_map():
    ip_folder_map = LevelDB("ip_folder_map")
    ip_folder_map.set(json.dumps({ "ip_folder_map": ip_folder_map}))
    ip_folder_map.save()

def update_ip_folder_map_by_ip(ips):
    ip_folder_map = get_ip_folder_map()
    old_ips = ip_folder_map.keys()
    if len(ips) > len(old_ips):
        new_ip = list(set(ips) - set(old_ips))[0]
        ip_folder_map[new_ip] = new_ip
    else:
        del_ip = list(set(old_ips) - set(ips))[0]
        folder = ip_folder_map[del_ip]
        del ip_folder_map[del_ip]
        if folder != del_ip:
            for k, v in ip_folder_map.iteritems():
                if k == v:
                    ip_folder_map[k] = folder
                    break
    set_ip_folder_map(ip_folder_map)

