# scanner/port_scanner.py
import socket
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, as_completed

from scanner.banner_grabber import grab_banner

COMMON_SERVICES = {
    20: "FTP-DATA", 21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP",
    53: "DNS", 80: "HTTP", 110: "POP3", 135: "RPC", 139: "NetBIOS",
    143: "IMAP", 443: "HTTPS", 445: "SMB", 3306: "MySQL",
    3389: "RDP", 5432: "PostgreSQL", 8080: "HTTP-Proxy"
}

def get_service_name(port: int) -> str:
    return COMMON_SERVICES.get(port, "Unknown")

def check_port(ip: str, port: int, timeout: float = 1.0) -> tuple[int, bool]:
    """Kiểm tra 1 port trên 1 IP."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        result = sock.connect_ex((ip, port))
        return port, result == 0
    except Exception:
        return port, False
    finally:
        sock.close()

def scan_host_ports(ip: str, ports: list[int] | range, max_threads: int = 100) -> list[dict]:
    """Quét đồng thời danh sách port trên một host và lấy banner dịch vụ."""
    open_ports = []
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        future_to_port = {executor.submit(check_port, ip, port): port for port in ports}
        for future in as_completed(future_to_port):
            port, is_open = future.result()
            if is_open:
                service = get_service_name(port)
                # Bóc tách banner dịch vụ thực tế
                banner = grab_banner(ip, port)
                open_ports.append({
                    "port": port,
                    "service": service,
                    "banner": banner
                })
    return sorted(open_ports, key=lambda x: x["port"])