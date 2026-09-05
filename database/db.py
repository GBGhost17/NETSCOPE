# database/db.py
import sqlite3
from datetime import datetime
from pathlib import Path

DB_DIR = Path(__file__).resolve().parent / "data"

# Tự động tạo thư mục 'data' nếu chưa tồn tại
DB_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DB_DIR / "netscope.db"

def get_connection():
    """Tạo kết nối tới SQLite và bật chế độ trả về Dict/Row."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Cho phép truy cập cột bằng tên thay vì index
    return conn

def init_db():
    """Khởi tạo cấu trúc các bảng."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target TEXT NOT NULL,
                scan_time REAL NOT NULL,
                created_at TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS hosts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_id INTEGER NOT NULL,
                ip TEXT NOT NULL,
                FOREIGN KEY (scan_id) REFERENCES scans(id) ON DELETE CASCADE
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                host_id INTEGER NOT NULL,
                port INTEGER NOT NULL,
                service TEXT NOT NULL,
                FOREIGN KEY (host_id) REFERENCES hosts(id) ON DELETE CASCADE
            )
        ''')
        conn.commit()

def save_scan(scan_report: dict) -> int:
    """Lưu toàn bộ kết quả phiên quét và trả về scan_id."""
    with get_connection() as conn:
        cursor = conn.cursor()
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute(
            "INSERT INTO scans (target, scan_time, created_at) VALUES (?, ?, ?)",
            (scan_report["target_network"], scan_report["scan_time"], created_at)
        )
        scan_id = cursor.lastrowid
        
        for ip, ports_info in scan_report["hosts"].items():
            cursor.execute(
                "INSERT INTO hosts (scan_id, ip) VALUES (?, ?)",
                (scan_id, ip)
            )
            host_id = cursor.lastrowid
            
            for p in ports_info:
                cursor.execute(
                    "INSERT INTO ports (host_id, port, service) VALUES (?, ?, ?)",
                    (host_id, p["port"], p["service"])
                )
        conn.commit()
        return scan_id

def get_scan_by_id(scan_id: int):
    """Lấy dữ liệu chi tiết của 1 scan_id phục vụ API."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM scans WHERE id = ?", (scan_id,))
        scan = cursor.fetchone()
        if not scan:
            return None
        
        result = {
            "id": scan["id"],
            "target": scan["target"],
            "scan_time": scan["scan_time"],
            "created_at": scan["created_at"],
            "hosts": {}
        }
        
        cursor.execute("SELECT id, ip FROM hosts WHERE scan_id = ?", (scan_id,))
        hosts = cursor.fetchall()
        
        for host in hosts:
            h_id = host["id"]
            ip = host["ip"]
            cursor.execute("SELECT port, service FROM ports WHERE host_id = ?", (h_id,))
            ports = cursor.fetchall()
            result["hosts"][ip] = [{"port": p["port"], "service": p["service"]} for p in ports]
            
        return result

def get_latest_two_scans():
    """Lấy 2 bản ghi gần nhất phục vụ so sánh (Diffing)."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM scans ORDER BY id DESC LIMIT 2")
        rows = cursor.fetchall()
        if len(rows) < 2:
            return None, None
        return rows[1]["id"], rows[0]["id"]

def get_all_scans():
    """Lấy danh sách tóm tắt tất cả các lần quét."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.id, s.target, s.scan_time, s.created_at, COUNT(h.id) as total_hosts
            FROM scans s
            LEFT JOIN hosts h ON s.id = h.scan_id
            GROUP BY s.id
            ORDER BY s.id DESC
        """)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


