
# scanner/monitor.py

def extract_ports(host_data) -> set[int]:
    """Trích xuất tập hợp port an toàn cho cả định dạng mới (dict) lẫn cũ (list)."""
    if isinstance(host_data, dict):
        port_list = host_data.get("ports", [])
    elif isinstance(host_data, list):
        port_list = host_data
    else:
        port_list = []
    
    return {p["port"] for p in port_list if isinstance(p, dict) and "port" in p}

def diff_scans(old_scan: dict, new_scan: dict) -> dict:
    """
    So sánh 2 phiên quét để tìm:
    - Thiết bị mới tham gia mạng (new_hosts)
    - Thiết bị rời mạng (offline_hosts)
    - Cổng mới mở / đóng trên các thiết bị vẫn online (port_changes)
    """
    if not old_scan or not new_scan:
        return {
            "new_hosts": [],
            "offline_hosts": [],
            "port_changes": {},
            "is_stable": True
        }

    old_hosts = set(old_scan.get("hosts", {}).keys())
    new_hosts = set(new_scan.get("hosts", {}).keys())

    new_devices = sorted(list(new_hosts - old_hosts))
    offline_devices = sorted(list(old_hosts - new_hosts))
    common_hosts = old_hosts & new_hosts

    port_changes = {}

    for ip in common_hosts:
        old_ports = extract_ports(old_scan["hosts"][ip])
        new_ports = extract_ports(new_scan["hosts"][ip])

        opened = sorted(list(new_ports - old_ports))
        closed = sorted(list(old_ports - new_ports))

        if opened or closed:
            port_changes[ip] = {
                "opened_ports": opened,
                "closed_ports": closed
            }

    is_stable = len(new_devices) == 0 and len(offline_devices) == 0 and len(port_changes) == 0

    return {
        "new_hosts": new_devices,
        "offline_hosts": offline_devices,
        "port_changes": port_changes,
        "is_stable": is_stable
    }