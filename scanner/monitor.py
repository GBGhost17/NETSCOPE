# scanner/monitor.py

def diff_scans(old_scan: dict, new_scan: dict) -> dict:
    """So sánh 2 kết quả scan và trả về dict chứa các biến động mạng."""
    old_hosts = set(old_scan["hosts"].keys())
    new_hosts = set(new_scan["hosts"].keys())
    
    newly_joined = list(new_hosts - old_hosts)
    disappeared = list(old_hosts - new_hosts)
    common_hosts = new_hosts & old_hosts
    
    port_changes = {}
    for ip in common_hosts:
        old_ports = {p["port"] for p in old_scan["hosts"][ip]}
        new_ports = {p["port"] for p in new_scan["hosts"][ip]}
        
        opened = list(new_ports - old_ports)
        closed = list(old_ports - new_ports)
        
        if opened or closed:
            port_changes[ip] = {
                "opened_ports": opened,
                "closed_ports": closed
            }
            
    return {
        "new_hosts": newly_joined,
        "offline_hosts": disappeared,
        "port_changes": port_changes,
        "is_stable": len(newly_joined) == 0 and len(disappeared) == 0 and len(port_changes) == 0
    }