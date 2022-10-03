import scapy.all as scapy
import requests
import socket

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip

def get_subnet(ip: str):
    return '.'.join(ip.split('.')[:2]) + '.0.0/24'

def scan_for_hub(subnet: str, port: int):
    run = True
    while run:
        devices = net_scan(subnet)
        for device in devices:
            ip = device['ip']
            print('Testing ip ', ip)
            try:
                response = requests.get(f'http://{ip}:{port}/api', timeout=5)
                response.raise_for_status()
                print('Hub Found')
                return ip
            except KeyboardInterrupt:
                run = False
                break
            except:
                pass

def net_scan(subnet: str):
    arp_req_frame = scapy.ARP(pdst = subnet)

    broadcast_ether_frame = scapy.Ether(dst = "ff:ff:ff:ff:ff:ff")
    
    broadcast_ether_arp_req_frame = broadcast_ether_frame / arp_req_frame

    answered_list = scapy.srp(broadcast_ether_arp_req_frame, timeout = 1, verbose = False)[0]
    result = [{'ip': '127.0.0.1'}]
    for i in range(0,len(answered_list)):
        client_dict = {'ip' : answered_list[i][1].psrc}
        result.append(client_dict)

    return result