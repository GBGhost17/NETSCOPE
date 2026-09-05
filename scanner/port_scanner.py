# scanner/port_scanner.py
import socket
import concurrent.futures

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
    """Quét danh sách port trên IP và trả về danh sách service."""
    open_ports = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = [executor.submit(check_port, ip, port) for port in ports]
        for future in concurrent.futures.as_completed(futures):
            port, is_open = future.result()
            if is_open:
                open_ports.append({
                    "port": port,
                    "service": get_service_name(port)
                })
                
    # Sắp xếp theo số hiệu port tăng dần
    return sorted(open_ports, key=lambda x: x["port"])