import requests
import typing
import socket
import ipaddress
import socket    
import logging
logger = logging.getLogger("network")

def get_my_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip

def map_network(my_ip: str) -> typing.List[str]:
    logger.info("Mapping network")
    
    # get my IP and compose a base like 192.168.1.xxx
    ip_parts = my_ip.split(".")
    base_ip = ip_parts[0] + "." + ip_parts[1] + "." + ip_parts[2]
    
    ip_list = ["127.0.0.1"]
    ip_list.extend([f"{base_ip}.{i}" for i in range(1, 255)])
    return ip_list

def get_subnet(ip: str) -> str:
    return str(ipaddress.ip_network(f"{ip}/255.255.255.0", strict=False))

def scan_for_hub(my_ip: str, port: int) -> str:
    run = True
    logger.info("Scanning for HUB")
    while run:
        devices = map_network(my_ip)
        for device in devices:
            url = f"http://{device}:{port}/api"
            logger.info(f"Testing: {device}")
            try:
                response = requests.get(url, timeout=5)
                response.raise_for_status()
                data = response.json()
                if "is_ova" in data:
                    logger.info(f"HUB Found at {device}!")
                    return device
            except requests.exceptions.ConnectionError as e:
                pass
