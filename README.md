# 🌐 NetScope — Network Reconnaissance & Security Audit Engine

[![Python Version](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED.svg)](https://www.docker.com/)
[![Database](https://img.shields.io/badge/SQLite-WAL%20Mode-003B57.svg)](https://www.sqlite.org/)
[![Release](https://img.shields.io/badge/release-v1.1.0-emerald.svg)](https://github.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**NetScope** là hệ thống trinh sát mạng cục bộ (LAN Reconnaissance), giám sát biến động thiết bị (Network Drift Detection) và đánh giá rủi ro an ninh mạng tự động. Ứng dụng kết hợp kiến trúc I/O bất đồng bộ hiệu năng cao (FastAPI, multi-threading) cùng Web Dashboard trực quan, hỗ trợ phân tích dữ liệu đa tầng từ Data Link (L2) đến Application (L7).

---

## ⚡ Tính Năng Cốt Lõi

### 1. Trinh Sát Mạng Đa Tầng (L2 - L7 Inspection)
* **Khám phá Host chuẩn xác (L3):** Quét toàn bộ dải mạng CIDR qua ICMP Ping đa luồng. Bóc tách thông số `TTL` từ phản hồi để loại bỏ triệt để hiện tượng nhận diện sai (False Positive) do ARP Cache trên Windows.
* **Định danh MAC & Nhà sản xuất (L2):** Phân tích bảng ARP Cache hệ thống (`arp -a` hoặc `/proc/net/arp`) để trích xuất địa chỉ MAC vật lý. Tự động đối chiếu tiền tố 24-bit OUI với cơ sở dữ liệu để nhận diện nhà sản xuất (Apple, Intel, TP-Link, Arcadyan...) và phát hiện cơ chế địa chỉ MAC ngẫu nhiên (Private/Randomized MAC).
* **Quét cổng TCP hiệu năng cao (L4):** Sử dụng TCP 3-Way Handshake kết hợp `ThreadPoolExecutor` để quét đồng thời danh sách cổng dịch vụ thông dụng (1–1000), rút ngắn thời gian thực thi xuống dưới 1 phút.
* **Thu thập Banner chủ động (L7):** Thực hiện kết nối socket chủ động để trích xuất chuỗi định danh dịch vụ và phiên bản web server thực tế (`Server: Apache/Nginx/mini_httpd...`).

### 2. Giám Sát Biến Động Mạng (Network Diffing Engine)
* Áp dụng lý thuyết tập hợp (Set Operations) để so sánh trạng thái giữa 2 phiên quét kế tiếp:
  * **Thiết bị mới:** Nhận diện các máy mới gia nhập mạng (`new_hosts`).
  * **Thiết bị rời mạng:** Phát hiện các thiết bị ngắt kết nối (`offline_hosts`).
  * **Thay đổi cổng:** Cảnh báo cổng dịch vụ mới mở hoặc vừa bị đóng trên từng thiết bị (`port_changes`).

### 3. Đánh Giá Rủi Ro & Chấm Điểm An Ninh (Security Scoring Engine)
* Chấm điểm an toàn mạng trên thang điểm **100** dựa trên chuẩn đánh giá an ninh (NIST/CIS).
* Phân loại rủi ro theo 4 cấp độ nghiêm trọng: `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`.
* Cảnh báo các cổng nguy hiểm: Telnet (23), SMB (445), RPC (135), NetBIOS (139), FTP (21), RDP (3389), MySQL (3306)...
* Phân hạng an toàn (`A`, `B`, `C`, `F`) và cung cấp khuyến nghị khắc phục chi tiết (Remediation) cho từng điểm yếu phát hiện được.

### 4. Giao Diện Giám Sát Thời Gian Thực (Dashboard UI)
* Thiết kế Dark Slate hiện đại, xây dựng bằng HTML5/CSS3 và Vanilla JavaScript (không phụ thuộc framework nặng).
* Cơ chế Polling theo dõi trạng thái và tiến độ quét (0% $\rightarrow$ 100%) mà không gây nghẽn kết nối.
* Xử lý triệt để lỗi bất đồng bộ **Race Condition** khi chuyển đổi phiên quét bằng kỹ thuật Request Sequence Tracking.

---

## 🛠️ Công Nghệ Sử Dụng

* **Ngôn ngữ:** Python 3.12+
* **Backend:** FastAPI, Uvicorn, Pydantic
* **DevOps & Containerization:** Docker, Docker Compose (Multi-stage build, Volume Data Persistence)
* **Network & Concurrency:** `socket`, `subprocess`, `concurrent.futures`, `ipaddress`
* **Cơ sở dữ liệu:** SQLite3 (Lưu trữ quan hệ phân cấp: `Scan -> Host -> Port`)
* **Frontend:** HTML5, CSS3, Vanilla JavaScript (Fetch API / Async-Await)
* **Testing:** `pytest`, unit testing chuẩn cho engine chấm điểm

---

## 📁 Cấu Trúc Dự Án

```text
NetScope/
├── backend/
│   ├── __init__.py
│   └── main.py                 # FastAPI Web Server, Background Tasks & REST API
├── database/
│   ├── __init__.py
│   ├── db.py                   # Kết nối SQLite, auto-migrations và CRUD helpers
│   └── data/
│       └── netscope.db         # File cơ sở dữ liệu SQLite (git ignored)
├── scanner/
│   ├── __init__.py
│   ├── host_discovery.py       # Ping Sweep đa luồng & phân tích TTL
│   ├── port_scanner.py         # Quét TCP Socket đa luồng & map dịch vụ
│   ├── mac_resolver.py         # Parse bảng ARP & tra cứu nhà sản xuất qua OUI
│   ├── banner_grabber.py       # Bóc tách L7 banner dịch vụ qua socket probe
│   ├── security_scorer.py      # Rule-based Engine chấm điểm an ninh & đề xuất khắc phục
│   └── monitor.py              # Thuật toán Diff so sánh trạng thái giữa 2 phiên quét
├── frontend/
│   ├── index.html              # Layout Dashboard
│   ├── style.css               # Định dạng giao diện Dark Slate & Severity Badges
│   └── app.js                  # Logic gọi API, Polling tiến độ & chống Race Condition
├── tests/
│   ├── __init__.py
│   ├── test_modules.py         # Kiểm thử tích hợp core scanner
│   └── test_security_scorer.py # Unit test thuật toán đánh giá rủi ro
├── .dockerignore               # Loại trừ cache, venv và database khỏi Docker build
├── Dockerfile                  # Đóng gói container ứng dụng (Debian-based Python 3.12)
├── docker-compose.yml          # Điều phối container, port mapping & volume mount
├── requirements.txt            # Danh sách thư viện phụ thuộc
└── README.md
```

---

## 🚀 Hướng Dẫn Cài Đặt & Chạy Ứng Dụng

### Cách 1: Triển khai nhanh bằng Docker (Khuyên dùng)

Hệ thống đã được container hóa trọn gói, tích hợp sẵn các gói mạng (`iputils-ping`, `net-tools`) và cơ chế Volume Mount lưu giữ dữ liệu SQLite bền vững trên máy host.

1. **Khởi chạy container:**
   ```bash
   docker compose up -d --build
   ```

2. **Kiểm tra trạng thái:**
   ```bash
   docker ps
   docker logs -f netscope-app
   ```

3. **Dừng hệ thống:**
   ```bash
   docker compose down
   ```

> **Ghi chú về kiến trúc mạng Docker:**
> * **Môi trường phát triển (Windows / macOS Docker Desktop):** Sử dụng ánh xạ cổng chuẩn `ports: ["8000:8000"]`.
> * **Môi trường Production (Linux Host / Server bare-metal):** Có thể chuyển sang `network_mode: host` trong file `docker-compose.yml` để container chia sẻ 100% stack mạng vật lý của host, cho phép đọc trực tiếp bảng ARP L2 nội bộ.

---

### Cách 2: Khởi chạy thủ công (Local Python Environment)

1. **Khởi tạo môi trường ảo:**
   ```bash
   # Tạo môi trường ảo
   python -m venv venv

   # Kích hoạt trên Windows PowerShell:
   .\venv\Scripts\Activate.ps1

   # Kích hoạt trên Linux/macOS:
   source venv/bin/activate
   ```

2. **Cài đặt các thư viện phụ thuộc:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Khởi chạy Server Backend:**
   ```bash
   uvicorn backend.main:app --reload
   ```

---

### Truy Cập Hệ Thống

* **Web Dashboard:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
* **Tài liệu API tương tác (Swagger UI):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 📡 REST API Specifications

| Phương thức | Endpoint | Mô tả |
| :--- | :--- | :--- |
| `POST` | `/api/scan` | Khởi động phiên quét mạng mới ở chế độ background task |
| `GET` | `/api/scan/status` | Kiểm tra tiến độ (%) và thông tin bước quét hiện tại |
| `GET` | `/api/scans` | Lấy danh sách lịch sử tất cả các phiên quét đã lưu |
| `GET` | `/api/scans/{scan_id}` | Lấy chi tiết thông tin một phiên quét (Hosts, Ports, MAC, Banner) |
| `GET` | `/api/scans/{scan_id}/security` | Xuất báo cáo đánh giá rủi ro an ninh mạng và danh mục khuyến nghị |
| `GET` | `/api/diff` | So sánh và phân tích biến động giữa 2 phiên quét gần nhất |

---

## 🧪 Kiểm Thử (Testing)

Dự án tích hợp sẵn các bộ kiểm thử độc lập cho core engine:

```bash
# Chạy kiểm thử tích hợp các module scanner
python tests/test_modules.py

# Chạy kiểm thử đơn vị cho Security Scorer
python tests/test_security_scorer.py
```

---