import requests
import socket
import ipaddress

import os
import socket    
import multiprocessing
import subprocess


def get_my_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip


def pinger(job_q, results_q):
    DEVNULL = open(os.devnull, 'w')
    while True:

        ip = job_q.get()

        if ip is None:
            break

        if os.name != 'nt':
            try:
                subprocess.check_call(['ping', '-c1', '-W1', ip], stdout=DEVNULL)
                results_q.put(ip)
                print(f'{ip} alive')
            except:
                pass
        else:
            try:
                subprocess.check_call(['ping', 'n 1', 'w 1', ip], stdout=DEVNULL)
                results_q.put(ip)
                print(f'{ip} alive')
            except:
                pass


def map_network(my_ip: str, pool_size=255):
    print('Mapping network')
    
    ip_list = ['127.0.0.1']
    
    # get my IP and compose a base like 192.168.1.xxx
    ip_parts = my_ip.split('.')
    base_ip = ip_parts[0] + '.' + ip_parts[1] + '.' + ip_parts[2] + '.'
    
    # prepare the jobs queue
    jobs = multiprocessing.Queue()
    results = multiprocessing.Queue()
    
    pool = [multiprocessing.Process(target=pinger, args=(jobs, results)) for i in range(pool_size)]
    
    for p in pool:
        p.start()
    
    # queue the ping processes
    for i in range(1, 255):
        jobs.put(base_ip + '{0}'.format(i))
    
    for p in pool:
        jobs.put(None)
    
    for p in pool:
        p.join()
    
    # collect the results
    while not results.empty():
        ip = results.get()
        ip_list.append(ip)

    return ip_list


def get_subnet(ip: str):
    return str(ipaddress.ip_network(f'{ip}/255.255.255.0', strict=False))


def scan_for_hub(my_ip: str, port: int):
    run = True
    print('Scanning for HUB')
    while run:
        devices = map_network(my_ip)
        for device in devices:
            url = f'http://{device}:{port}/api'
            print('Testing: ', url)
            try:
                response = requests.get(url, timeout=5)
                response.raise_for_status()
                print('Hub Found')
                return device
            except requests.exceptions.ConnectionError as e:
                pass
