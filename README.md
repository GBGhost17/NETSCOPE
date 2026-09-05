# NetScope - Network Security Scanner

NetScope là một công cụ quét mạng hiện đại được xây dựng với Python, FastAPI và SQLAlchemy.

## Tính năng

- Khám phá host trong mạng
- Quét port trên các host
- Phát hiện service chạy trên port
- API REST để quản lý các scan

## Cấu trúc dự án

```
netscope/
├── scanner/          # Các module quét mạng
├── backend/          # API FastAPI
├── database/         # Model và cấu hình database
├── frontend/         # Giao diện web
├── tests/            # Các test
└── requirements.txt  # Dependencies
```

## Cài đặt

1. Tạo virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

2. Cài đặt dependencies:
```bash
pip install -r requirements.txt
```

3. Chạy ứng dụng:
```bash
python netscope/backend/main.py
```

## API Endpoints

- `POST /scan` - Tạo một scan mới
- `GET /scan/{id}` - Lấy kết quả scan

## Giấy phép

MIT
