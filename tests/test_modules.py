# tests/test_modules.py
import sys
from pathlib import Path

# Thêm thư mục gốc của dự án vào sys.path để import scanner và database không bị lỗi
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def run_tests():
    print("=" * 50)
    print("  BẮT ĐẦU KIỂM TRA TÍCH HỢP HỆ THỐNG NETSCOPE")
    print("=" * 50)

    # -------------------------------------------------------------
    # TEST 1: Kiểm tra Import các module
    # -------------------------------------------------------------
    print("\n[TEST 1] Kiểm tra Import các module...")
    try:
        from database.db import init_db, save_scan, get_scan_by_id, get_all_scans, get_latest_two_scans
        from scanner.host_discovery import ping_host, discover_hosts
        from scanner.port_scanner import check_port, scan_host_ports, get_service_name
        from scanner.monitor import diff_scans
        print("  --> [PASS] Đã import thành công tất cả các module!")
    except ModuleNotFoundError as e:
        print(f"  --> [FAIL] Lỗi import module: {e}")
        print("      Gợi ý: Kiểm tra file __init__.py trong các thư mục scanner/ và database/")
        return

    # -------------------------------------------------------------
    # TEST 2: Kiểm tra Database (Init -> Save -> Query)
    # -------------------------------------------------------------
    print("\n[TEST 2] Kiểm tra Database CRUD...")
    try:
        init_db()
        print("  --> [PASS] init_db() tạo bảng thành công.")

        # Tạo bản ghi quét mẫu A
        mock_scan_a = {
            "target_network": "192.168.1.1/24",
            "scan_time": 12.5,
            "hosts": {
                "192.168.1.1": [{"port": 53, "service": "DNS"}, {"port": 80, "service": "HTTP"}],
                "192.168.1.3": [{"port": 445, "service": "SMB"}]
            }
        }
        id_a = save_scan(mock_scan_a)
        print(f"  --> [PASS] save_scan() lưu thành công bản ghi #{id_a}.")

        # Đọc lại bản ghi vừa lưu
        retrieved_a = get_scan_by_id(id_a)
        assert retrieved_a is not None, "Không tìm thấy bản ghi vừa lưu!"
        assert "192.168.1.1" in retrieved_a["hosts"], "Thiếu host trong dữ liệu trả về!"
        assert len(retrieved_a["hosts"]["192.168.1.1"]) == 2, "Sai số lượng port!"
        print(f"  --> [PASS] get_scan_by_id(#{id_a}) dữ liệu toàn vẹn và chính xác.")

    except Exception as e:
        print(f"  --> [FAIL] Lỗi Database: {e}")
        return

    # -------------------------------------------------------------
    # TEST 3: Kiểm tra Thuật toán So sánh (scanner/monitor.py)
    # -------------------------------------------------------------
    print("\n[TEST 3] Kiểm tra Module So sánh (Diffing Engine)...")
    try:
        # Tạo bản ghi quét mẫu B (có biến động so với A)
        mock_scan_b = {
            "target_network": "192.168.1.1/24",
            "scan_time": 14.2,
            "hosts": {
                "192.168.1.1": [
                    {"port": 53, "service": "DNS"}, 
                    {"port": 80, "service": "HTTP"},
                    {"port": 443, "service": "HTTPS"}  # Port mới mở
                ],
                "192.168.1.9": []                      # Host mới vào mạng
            }
        }
        id_b = save_scan(mock_scan_b)
        scan_a_data = get_scan_by_id(id_a)
        scan_b_data = get_scan_by_id(id_b)

        diff = diff_scans(scan_a_data, scan_b_data)

        # Kiểm tra logic
        assert "192.168.1.9" in diff["new_hosts"], "Không phát hiện host mới!"
        assert "192.168.1.3" in diff["offline_hosts"], "Không phát hiện host offline!"
        assert 443 in diff["port_changes"]["192.168.1.1"]["opened_ports"], "Không phát hiện port 443 mới mở!"
        assert diff["is_stable"] is False, "Cờ is_stable phải là False khi có biến động!"
        print("  --> [PASS] diff_scans() phát hiện chính xác biến động mạng:")
        print(f"      + Thiết bị mới: {diff['new_hosts']}")
        print(f"      - Thiết bị offline: {diff['offline_hosts']}")
        print(f"      * Cổng mới mở trên 192.168.1.1: {diff['port_changes']['192.168.1.1']['opened_ports']}")

    except Exception as e:
        print(f"  --> [FAIL] Lỗi module monitor: {e}")
        return

    # -------------------------------------------------------------
    # TEST 4: Kiểm tra nhanh Port Scanner & Host Discovery trên Localhost
    # -------------------------------------------------------------
    print("\n[TEST 4] Kiểm tra hàm quét thực tế (Localhost 127.0.0.1)...")
    try:
        # Test ping chính máy mình
        ip, is_alive = ping_host("127.0.0.1")
        print(f"  --> Ping 127.0.0.1: {'Thành công (Online)' if is_alive else 'Thất bại'}")

        # Test socket với 1 port dummy
        port, is_open = check_port("127.0.0.1", 65432, timeout=0.2)
        print(f"  --> Check Port 65432 trên 127.0.0.1: {'OPEN' if is_open else 'CLOSED'} (Socket hoạt động bình thường)")
        
        # Test mapping service name
        assert get_service_name(80) == "HTTP", "Sai mapping port 80!"
        assert get_service_name(9999) == "Unknown", "Sai fallback Unknown service!"
        print("  --> [PASS] Service mapping hoạt động chuẩn.")

    except Exception as e:
        print(f"  --> [FAIL] Lỗi quét: {e}")
        return

    print("\n" + "=" * 50)
    print("  🎉 TẤT CẢ MODULE ĐÃ LIÊN KẾT HOÀN HẢO!")
    print("  Sẵn sàng 100% để tích hợp vào FastAPI.")
    print("=" * 50)

if __name__ == "__main__":
    run_tests()