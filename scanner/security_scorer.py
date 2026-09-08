
# scanner/security_scorer.py

# Bảng quy tắc đánh giá rủi ro theo số hiệu cổng
PORT_RISK_RULES = {
    # CRITICAL RISK (-25 điểm)
    23: {
        "name": "Telnet",
        "severity": "CRITICAL",
        "penalty": 25,
        "description": "Giao thức truyền dữ liệu dạng văn bản thuần (plain-text), dễ bị nghe lén tài khoản/mật khẩu.",
        "remediation": "Vô hiệu hóa Telnet và chuyển sang sử dụng SSH (Port 22) có mã hóa."
    },
    445: {
        "name": "SMB",
        "severity": "HIGH",
        "penalty": 15,
        "description": "Cổng chia sẻ file Windows SMB, mục tiêu khai thác của các mã độc tống tiền (WannaCry / EternalBlue).",
        "remediation": "Chặn port 445 ở tường lửa nếu không chia sẻ tệp nội bộ; luôn cập nhật bản vá Windows mới nhất."
    },
    135: {
        "name": "Microsoft RPC",
        "severity": "MEDIUM",
        "penalty": 10,
        "description": "Dịch vụ Remote Procedure Call của Windows, thường bị dò quét để khai thác leo thang đặc quyền.",
        "remediation": "Cấu hình Windows Firewall chặn truy cập RPC từ các dải mạng không tin cậy."
    },
    139: {
        "name": "NetBIOS",
        "severity": "MEDIUM",
        "penalty": 10,
        "description": "NetBIOS Session Service tiết lộ thông tin cấu trúc máy tính và tên NetBIOS nội bộ.",
        "remediation": "Tắt tính năng NetBIOS over TCP/IP trong thuộc tính card mạng nếu không dùng ứng dụng cũ."
    },
    21: {
        "name": "FTP",
        "severity": "HIGH",
        "penalty": 15,
        "description": "FTP truyền thông tin đăng nhập không mã hóa qua mạng.",
        "remediation": "Chuyển sang SFTP (qua SSH) hoặc FTPS (FTP over TLS/SSL)."
    },
    3389: {
        "name": "RDP",
        "severity": "HIGH",
        "penalty": 15,
        "description": "Remote Desktop mở trực tiếp đối mặt nguy cơ bị tấn công brute-force mật khẩu.",
        "remediation": "Bật Network Level Authentication (NLA) hoặc đặt RDP sau VPN nội bộ."
    },
    80: {
        "name": "HTTP",
        "severity": "LOW",
        "penalty": 5,
        "description": "Giao thức web chưa mã hóa, thiếu chứng chỉ bảo mật SSL/TLS.",
        "remediation": "Chuyển hướng toàn bộ lưu lượng web sang HTTPS (Port 443)."
    },
    3306: {
        "name": "MySQL",
        "severity": "HIGH",
        "penalty": 15,
        "description": "Cổng cơ sở dữ liệu MySQL lắng nghe trực tiếp trên mạng LAN.",
        "remediation": "Chỉ bind cơ sở dữ liệu trên localhost (127.0.0.1) trừ khi cần cluster."
    }
}

def evaluate_network_security(hosts_data: dict) -> dict:
    """
    Phân tích toàn bộ dữ liệu quét để tính điểm bảo mật tổng thể (Security Score)
    và tổng hợp danh sách các lỗ hổng/cảnh báo an ninh.
    """
    score = 100
    findings = []
    
    for ip, info in hosts_data.items():
        ports = info.get("ports", [])
        for p in ports:
            port_num = p["port"]
            if port_num in PORT_RISK_RULES:
                rule = PORT_RISK_RULES[port_num]
                score -= rule["penalty"]
                findings.append({
                    "ip": ip,
                    "port": port_num,
                    "service": rule["name"],
                    "severity": rule["severity"],
                    "penalty": rule["penalty"],
                    "description": rule["description"],
                    "remediation": rule["remediation"]
                })
                
    score = max(0, score)
    
    # Ranking
    if score >= 85:
        grade = "A"
        status = "An toàn (Low Risk)"
    elif score >= 70:
        grade = "B"
        status = "Khá (Moderate Risk)"
    elif score >= 50:
        grade = "C"
        status = "Cần chú ý (Elevated Risk)"
    else:
        grade = "F"
        status = "Nguy hiểm (High Risk)"
        
    return {
        "score": score,
        "grade": grade,
        "status": status,
        "total_issues": len(findings),
        "findings": findings
    }
    