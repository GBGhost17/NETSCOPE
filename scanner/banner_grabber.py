
# scanner/banner_grabber.py
import socket
import re

def grab_banner(ip: str, port: int, timeout: float = 1.0) -> str:
    """
    Gửi payload thăm dò hoặc đọc chuỗi phản hồi ban đầu từ cổng dịch vụ.
    Trả về chuỗi banner sạch (rút gọn), hoặc rỗng nếu không có dữ liệu.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    
    banner = ""
    try:
        s.connect((ip, port))
        
        # 1. Nhóm dịch vụ Web (HTTP / HTTPS / Proxy)
        if port in [80, 8080, 8000, 8888]:
            probe = f"HEAD / HTTP/1.1\r\nHost: {ip}\r\nUser-Agent: NetScope/1.0\r\nConnection: close\r\n\r\n"
            s.sendall(probe.encode("latin-1", errors="ignore"))
            response = s.recv(1024).decode("latin-1", errors="ignore")
            
            # Trích xuất giá trị header 'Server:'
            match = re.search(r"Server:\s*([^\r\n]+)", response, re.IGNORECASE)
            if match:
                return match.group(1).strip()
            
            # Fallback lấy dòng trạng thái đầu tiên (VD: HTTP/1.1 200 OK)
            first_line = response.split("\r\n")[0].strip()
            return first_line if first_line else ""

        # 2. Nhóm dịch vụ tự động trả về greeting banner (SSH, FTP, SMTP)
        # Các dịch vụ này sẽ tự gửi thông điệp chào ngay khi socket vừa connect
        response = s.recv(1024).decode("latin-1", errors="ignore").strip()
        if response:
            # Lấy dòng đầu tiên và loại bỏ ký tự điều khiển rác
            first_line = response.split("\n")[0].strip()
            return first_line[:120]
            
        # 3. Fallback cho các cổng khác: gửi ký tự xuống dòng để kích hoạt phản hồi
        s.sendall(b"\r\n\r\n")
        response = s.recv(512).decode("latin-1", errors="ignore").strip()
        if response:
            return response.split("\n")[0].strip()[:120]

    except Exception:
        pass
    finally:
        s.close()

    return ""



