# scanner/host_discovery.py
import subprocess
import platform
import ipaddress
import concurrent.futures

def ping_host(ip: str) -> tuple[str, bool]:
    """Ping một IP cụ thể, kiểm tra cờ TTL."""
    is_windows = platform.system().lower() == 'windows'
    command = ['ping', '-n', '1', '-w', '500', str(ip)] if is_windows else ['ping', '-c', '1', '-W', '1', str(ip)]
    
    try:
        response = subprocess.run(
            command, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            timeout=1.5
        )
        output = response.stdout.lower()
        if "ttl=" in output and "unreachable" not in output:
            return str(ip), True
        return str(ip), False
    except Exception:
        return str(ip), False

def discover_hosts(network_cidr: str, max_threads: int = 50) -> list[str]:
    """Quét dải mạng và trả về danh sách các IP đang Online."""
    network = ipaddress.ip_network(network_cidr, strict=False)
    hosts_to_scan = list(network.hosts())
    
    active_hosts = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = [executor.submit(ping_host, str(ip)) for ip in hosts_to_scan]
        for future in concurrent.futures.as_completed(futures):
            ip, is_alive = future.result()
            if is_alive:
                active_hosts.append(ip)
                
    # Sắp xếp lại IP theo thứ tự số tăng dần cho đẹp mắt
    return sorted(active_hosts, key=lambda x: [int(part) for part in x.split('.')])