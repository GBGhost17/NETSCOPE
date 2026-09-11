# scanner/mac_resolver.py

import os
import re
import subprocess
import platform

OUI_DATABASE = {
    # Apple
    "AC:DE:48": "Apple, Inc.", "F0:18:98": "Apple, Inc.", "BC:D0:74": "Apple, Inc.",
    "A4:83:E7": "Apple, Inc.", "00:17:F2": "Apple, Inc.", "34:36:3B": "Apple, Inc.",
    
    # Samsung
    "30:07:4D": "Samsung Electronics", "50:01:D9": "Samsung Electronics",
    "A8:9C:ED": "Samsung Electronics", "D0:B5:C2": "Samsung Electronics",
    
    # Thiết bị mạng / Router
    "50:C7:BF": "TP-Link Technologies", "74:DA:38": "TP-Link Technologies",
    "F4:F2:6D": "TP-Link Technologies", "E4:18:6B": "TP-Link Technologies",
    "04:42:1A": "ASUSTek Computer", "10:7B:44": "ASUSTek Computer",
    "00:0C:43": "Ralink / MediaTek", "20:4E:7F": "Netgear Inc.",
    "7C:7B:68": "Arcadyan / Carrier Router",
    "A0:65:18": "VNPT Technology",
    "68:A0:F6": "Viettel Network",
    
    # Xiaomi / IoT
    "64:90:C1": "Xiaomi Communications", "E8:48:B8": "Xiaomi Communications",
    "84:D8:1B": "Espressif Systems (ESP/IoT)", "24:6F:28": "Espressif Systems (ESP/IoT)",
    "B8:27:EB": "Raspberry Pi Foundation", "DC:A6:32": "Raspberry Pi Foundation",
    
    # Máy tính / Card mạng / Virtualization
    "00:1A:2B": "Intel Corporate", "18:65:90": "Intel Corporate",
    "B8:85:84": "Dell Inc.", "00:14:22": "Dell Inc.",
    "D8:47:32": "HP Inc.", "00:50:56": "VMware Virtual Adapter",
    "08:00:27": "Oracle VirtualBox", "00:15:5D": "Microsoft Hyper-V"
}

def get_system_arp_table() -> dict[str, str]:
    """
    Đọc bảng ARP cache hệ thống và trả về dict {IP: MAC}.
    Hỗ trợ Windows, Linux/macOS và Docker container.
    """
    arp_table = {}

    # Cách 1: Đọc trực tiếp từ kernel Linux nếu chạy trong Container
    if os.path.exists("/proc/net/arp"):
        try:
            with open("/proc/net/arp", "r", encoding="utf-8") as f:
                lines = f.readlines()[1:]  # Bỏ dòng header
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 4:
                        ip, flags, mac = parts[0], parts[2], parts[3]
                        # 0x2 tương đương cờ ATF_COM (hợp lệ/hoàn thành)
                        if flags != "0x0" and mac != "00:00:00:00:00:00":
                            arp_table[ip] = mac.upper()
            if arp_table:
                return arp_table
        except Exception:
            pass

    # Cách 2: Parse lệnh CLI 'arp -a' đa nền tảng
    try:
        output = subprocess.check_output(["arp", "-a"], text=True, stderr=subprocess.DEVNULL)
        
        # Regex hỗ trợ cả format:
        # Windows: "192.168.1.1        7c-7b-68-e1-c2-c0"
        # Linux:   "? (192.168.1.1) at 7c:7b:68:e1:c2:c0 [ether]"
        pattern = r"\(?([0-9]{1,3}(?:\.[0-9]{1,3}){3})\)?\s+(?:at\s+)?([0-9a-fA-F]{2}(?:[:-][0-9a-fA-F]{2}){5})"
        matches = re.findall(pattern, output)
        
        for ip, raw_mac in matches:
            mac_clean = raw_mac.replace("-", ":").upper()
            if not mac_clean.startswith("FF:FF:FF") and not ip.startswith("224.") and not ip.endswith(".255"):
                arp_table[ip] = mac_clean
    except Exception:
        pass

    return arp_table

def resolve_vendor(mac: str) -> str:
    """Tra cứu hãng sản xuất từ 3 byte đầu tiên (OUI prefix) của địa chỉ MAC."""
    if not mac or mac == "Unknown":
        return "Unknown Device"
    
    prefix = ":".join(mac.split(":")[:3]).upper()
    return OUI_DATABASE.get(prefix, "Generic / Unregistered Vendor")