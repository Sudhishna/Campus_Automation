import time
import re
import subprocess
from ansible.parsing.dataloader import DataLoader
from ansible.inventory.manager import InventoryManager
from campus_config import Campus_Config
from subprocess import call

campus_config = Campus_Config()

file_name = "/home/ubuntu/Evolved_Campus_Core_Automation/Inventory"

with open(file_name) as f:
    content = f.read()
    campuses = re.findall('\[(.*?)\]',content)

campus_info = {}
leaf = []
spine = []

for campus in campuses:
    if "children" in campus:
        campus_id = campus.rsplit(":",1)[0]
        campus_info.update({campus_id: {'leaf': None,'spine':None}})

for campus in campuses:
    leaf_count = 0
    spine_count = 0
    campus_id = campus.rsplit("-")[1]
    if not "children"in campus:
        if "leaf" in campus:
            data_loader = DataLoader()
            inventory = InventoryManager(loader = data_loader,
                                         sources=[file_name])
            lst = inventory.get_groups_dict()[campus]
            for ls in lst:
                leaf.append(ls + "_" + campus_id)
                leaf_count += 1
            campus_info['campus-' + campus_id]['leaf'] = leaf_count
        elif "spine" in campus:
            data_loader = DataLoader()
            inventory = InventoryManager(loader = data_loader,
                                         sources=[file_name])
            lst = inventory.get_groups_dict()[campus] 
            for ls in lst:
                spine.append(ls + "_" + campus_id)
                spine_count += 1
            campus_info['campus-' + campus_id]['spine'] = spine_count

print campus_info

dev_ips = []
for campus in campuses:
    if "children"in campus:
        campus_id = campus.split(":")[0]
        id = campus_id.split("-")[1]
        
        data_loader = DataLoader()
        inventory = InventoryManager(loader = data_loader,
                                     sources=[file_name])
        for dev in inventory.get_groups_dict()[campus_id]:
            dev_ips.append(dev + "_" + id)

process = subprocess.Popen(["ansible-playbook", "-i", "Inventory", "server_lldp.yml", "--extra-vars", "ansible_sudo_pass=Clouds123"], stdout=subprocess.PIPE)
server_info, err = process.communicate()
print server_info

server_ip_hostname = re.findall(r"\"ps.stdout,inventory_hostname\": \"\((.*)\)\"",server_info)
print server_ip_hostname
server_hostip_map = {}
for servers in server_ip_hostname:
    servers = servers.split(",")
    server_name = ''
    server_ip = ''
    for server in servers:
        if "server" in server:
            server_name = server.replace("'","")
            server_name = server_name.replace("u","")
        else:
            server_ip = server.replace("'","")
            server_ip = server_ip.replace("u","")

    server_hostip_map.update({server_name.strip(): server_ip.strip()})
print server_hostip_map

servers = []
for campus in campuses:
    if "server"in campus:
        campus_id = campus.split(":")[0]
        id = campus_id.split("-")[1]

        data_loader = DataLoader()
        inventory = InventoryManager(loader = data_loader,
                                     sources=[file_name])
        for dev in inventory.get_groups_dict()[campus_id]:
            servers.append(dev + "_" + id)

##dev = campus_config.enable_lldp(dev_ips)

print "Please wait for the devices to establish the links...."
##time.sleep(45)

dev = campus_config.campus_underlay(spine,leaf,servers,campus_info,server_hostip_map)

