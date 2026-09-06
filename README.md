# NetScope — Network Scanner & Monitoring System

NetScope là hệ thống quét và giám sát mạng nội bộ (LAN) theo thời gian thực được xây dựng bằng **Python**, **FastAPI**, và **SQLite**. Hệ thống kết hợp lập trình mạng tầng socket, xử lý bất đồng bộ đa luồng (multi-threading) và thuật toán giám sát biến động (Diffing Engine) để theo dõi trạng thái thiết bị và cổng dịch vụ trên giao diện Web Dashboard.

---

## ⚡ Tính năng nổi bật

* **Khám phá mạng chuẩn xác (Host Discovery):** Quét toàn bộ dải mạng CIDR qua ICMP Ping. Bóc tách thông số `TTL` từ phản hồi để loại bỏ triệt để hiện tượng nhận diện sai (False Positive) do ARP Cache trên Windows.
* **Quét cổng dịch vụ đồng thời (Multi-threaded Port Scanner):** Sử dụng TCP 3-Way Handshake kết hợp `ThreadPoolExecutor` để quét dải 1.000 port thông dụng trên nhiều host cùng lúc, rút ngắn thời gian thực thi xuống dưới 1 phút.
* **Nhận diện dịch vụ (Service Detection):** Tự động ánh xạ số hiệu cổng sang tên dịch vụ tương ứng (DNS, HTTP, HTTPS, SMB, RPC, RDP, MySQL...).
* **Công cụ giám sát biến động (Network Diffing Engine):** Áp dụng lý thuyết tập hợp (Set Operations) để so sánh trạng thái giữa các lần quét, cảnh báo thiết bị lạ gia nhập mạng, thiết bị offline hoặc thay đổi trạng thái cổng dịch vụ.
* **Kiến trúc Asynchronous & Polling:** Đẩy tác vụ I/O mạng nặng vào `BackgroundTasks` của FastAPI; giao diện web cập nhật tiến trình liên tục qua cơ chế Polling mà không làm nghẽn server.
* **Lưu trữ quan hệ phân cấp:** Lưu vết toàn bộ lịch sử quét vào SQLite theo cấu trúc quan hệ 1-N: `Scan -> Host -> Port`.

---

## 🛠️ Công nghệ sử dụng

* **Ngôn ngữ:** Python 3.12+
* **Backend:** FastAPI, Uvicorn, Pydantic
* **Network & Concurrency:** `socket`, `subprocess`, `concurrent.futures`, `ipaddress`
* **Cơ sở dữ liệu:** SQLite3 (`sqlite3` native module)
* **Frontend:** HTML5, CSS3 (Modern Dark Slate), Vanilla JavaScript (Async/Await Fetch API)

---

## 📁 Cấu trúc dự án

```
NetScope/
├── backend/
│   ├── __init__.py
│   └── main.py                 # REST API endpoints & background task pipeline
├── database/
│   ├── __init__.py
│   ├── db.py                   # Kết nối SQLite và các hàm CRUD
│   └── data/
│       └── netscope.db         # File cơ sở dữ liệu SQLite (git ignored)
├── scanner/
│   ├── __init__.py
│   ├── host_discovery.py       # Logic Ping Sweep & kiểm tra cờ TTL
│   ├── port_scanner.py         # Quét TCP Socket đa luồng & map dịch vụ
│   └── monitor.py              # Thuật toán Diff so sánh 2 phiên quét
├── frontend/
│   ├── index.html              # Web Dashboard layout
│   ├── style.css               # Giao diện Dark Slate
│   └── app.js                  # Logic gọi API và Polling tiến độ quét
├── tests/
│   ├── __init__.py
│   └── test_modules.py         # Bộ kiểm thử tích hợp (Integration Tests)
├── pre-project/                # Kịch bản thử nghiệm giai đoạn PoC
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🚀 Hướng dẫn cài đặt & Chạy ứng dụng

**1. Khởi tạo môi trường ảo (Virtual Environment):**

``` bash
# Tạo môi trường ảo
python -m venv venv

# Kích hoạt trên Windows PowerShell:
.\venv\Scripts\Activate.ps1

# Kích hoạt trên Linux/macOS:
source venv/bin/activate
```

**2. Cài đặt các thư viện phụ thuộc:**

```bash
pip install -r requirements.txt
```

**3. Khởi chạy Server FastAPI:**

```bash
uvicorn backend.main:app --reload
```

**4. Truy cập hệ thống:**

* **Web Dashboard:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
* **Tài liệu API tương tác (Swagger UI):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 📡 REST API Specifications

| Phương thức | Endpoint | Mô tả |
| :--- | :--- | :--- |
| `POST` | `/api/scan` | Khởi động phiên quét mạng mới ở chế độ background |
| `GET` | `/api/scan/status` | Kiểm tra tiến độ (%) và bước thực thi hiện tại |
| `GET` | `/api/scans` | Lấy danh sách tóm tắt toàn bộ lịch sử các phiên quét |
| `GET` | `/api/scans/{scan_id}` | Lấy chi tiết toàn bộ máy và cổng mở của một phiên quét |
| `GET` | `/api/diff` | So sánh và phân tích biến động giữa 2 phiên quét gần nhất |

---

## 🧪 Kiểm thử tích hợp (Integration Tests)

Chạy kịch bản kiểm tra toàn vẹn giữa các module:

```bash
python tests/test_modules.py
```

Bộ test tự động xác thực:
1. Tính tương thích khi import các package nội bộ.
2. Thao tác CRUD và tính toàn vẹn khóa ngoại trên Database SQLite.
3. Thuật toán Set Difference của module `diff_scans`.
4. Khả năng kết nối Socket TCP và ICMP Ping trên `127.0.0.1`.