# backend/main.py

import time
from pathlib import Path
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from database.db import (
    init_db,
    save_scan,
    get_scan_by_id,
    get_all_scans,
    get_latest_two_scans
)
from scanner.host_discovery import discover_hosts
from scanner.port_scanner import scan_host_ports
from scanner.mac_resolver import get_system_arp_table, resolve_vendor
from scanner.monitor import diff_scans
from scanner.security_scorer import evaluate_network_security
from backend.scheduler import scheduler

app = FastAPI(
    title="NetScope API",
    description="Hệ thống quét và giám sát mạng nội bộ thời gian thực",
    version="1.2.0"
)

# Config CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()

# Background scan status tracker
SCAN_STATE = {
    "is_running": False,
    "target": None,
    "step": "Sẵn sàng",
    "progress": 0,
    "last_scan_id": None,
    "error": None
}

class ScanRequest(BaseModel):
    target: str = "192.168.2.1/24"

class ScheduleConfigRequest(BaseModel):
    target: str = "192.168.2.1/24"
    interval_minutes: int = 30

def background_scan_pipeline(target_network: str):
    """Pipeline quét mạng tuần tự từ L2 đến L7 và lưu kết quả vào database."""
    global SCAN_STATE
    try:
        SCAN_STATE["is_running"] = True
        SCAN_STATE["target"] = target_network
        SCAN_STATE["step"] = "Đang khởi tạo..."
        SCAN_STATE["progress"] = 5
        SCAN_STATE["error"] = None
        start_time = time.time()

        # Bước 1: Khám phá Host (ICMP Ping Sweep)
        SCAN_STATE["step"] = f"Đang dò tìm thiết bị trong dải {target_network}..."
        SCAN_STATE["progress"] = 20
        alive_hosts = discover_hosts(target_network)

        # Trích xuất bảng ARP cache ngay sau khi vừa ping hoàn tất
        arp_table = get_system_arp_table()

        # Bước 2: Quét cổng TCP & Trích xuất Banner
        SCAN_STATE["step"] = f"Phát hiện {len(alive_hosts)} máy Online. Bắt đầu quét cổng..."
        SCAN_STATE["progress"] = 50

        ports_to_scan = range(1, 1001)
        hosts_data = {}

        for idx, ip in enumerate(alive_hosts, 1):
            SCAN_STATE["step"] = f"Đang quét port máy {ip} ({idx}/{len(alive_hosts)})..."
            open_ports = scan_host_ports(ip, ports_to_scan)

            mac = arp_table.get(ip, "Unknown")
            vendor = resolve_vendor(mac) if mac != "Unknown" else "This Machine / Gateway"

            hosts_data[ip] = {
                "mac": mac,
                "vendor": vendor,
                "ports": open_ports
            }

        # Bước 3: Tổng hợp và lưu Database
        SCAN_STATE["step"] = "Đang tổng hợp và lưu kết quả vào Database..."
        SCAN_STATE["progress"] = 90

        scan_report = {
            "target_network": target_network,
            "scan_time": round(time.time() - start_time, 2),
            "hosts": hosts_data
        }

        scan_id = save_scan(scan_report)

        SCAN_STATE["step"] = "Hoàn tất!"
        SCAN_STATE["progress"] = 100
        SCAN_STATE["last_scan_id"] = scan_id

    except Exception as e:
        SCAN_STATE["error"] = str(e)
        SCAN_STATE["step"] = f"Lỗi: {str(e)}"
    finally:
        SCAN_STATE["is_running"] = False


# ================= REST API ENDPOINTS =================

@app.post("/api/scan", summary="Bắt đầu quét mạng thủ công (Chạy ngầm)")
def start_scan(request: ScanRequest, background_tasks: BackgroundTasks):
    global SCAN_STATE
    if SCAN_STATE["is_running"]:
        raise HTTPException(status_code=400, detail="Có phiên quét khác đang chạy.")

    background_tasks.add_task(background_scan_pipeline, request.target)
    return {"message": "Tiến trình quét đã bắt đầu", "target": request.target}

@app.get("/api/scan/status", summary="Kiểm tra tiến độ quét")
def get_scan_status():
    return SCAN_STATE

@app.get("/api/scans", summary="Lịch sử các phiên quét")
def list_scans():
    return get_all_scans()

@app.get("/api/scans/{scan_id}", summary="Chi tiết phiên quét theo ID")
def get_scan_detail(scan_id: int):
    data = get_scan_by_id(scan_id)
    if not data:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiên quét.")
    return data

@app.get("/api/diff", summary="So sánh 2 lần quét gần nhất")
def compare_latest_scans():
    old_id, new_id = get_latest_two_scans()
    if not old_id or not new_id:
        return {"message": "Cần tối thiểu 2 phiên quét trong database để so sánh."}

    old_data = get_scan_by_id(old_id)
    new_data = get_scan_by_id(new_id)

    diff_result = diff_scans(old_data, new_data)
    return {
        "old_scan": {"id": old_data["id"], "time": old_data["created_at"]},
        "new_scan": {"id": new_data["id"], "time": new_data["created_at"]},
        "changes": diff_result
    }

@app.get("/api/scans/{scan_id}/security", summary="Đánh giá rủi ro và chấm điểm an ninh mạng cho phiên quét")
def get_security_audit(scan_id: int):
    scan_data = get_scan_by_id(scan_id)
    if not scan_data:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiên quét.")

    audit_report = evaluate_network_security(scan_data["hosts"])
    return {
        "scan_id": scan_id,
        "target": scan_data["target"],
        "created_at": scan_data["created_at"],
        "audit": audit_report
    }

# ================= SCHEDULER ENDPOINTS =================

@app.get("/api/scheduler", summary="Lấy trạng thái cấu hình lịch quét tự động")
async def get_scheduler_status():
    return scheduler.get_status()

@app.post("/api/scheduler/start", summary="Kích hoạt lập lịch quét định kỳ")
async def start_scheduler(config: ScheduleConfigRequest):
    if SCAN_STATE["is_running"]:
        raise HTTPException(status_code=400, detail="Hệ thống đang bận thực hiện phiên quét khác.")

    scheduler.start(
        target=config.target,
        interval_minutes=config.interval_minutes,
        scan_fn=background_scan_pipeline
    )
    return {
        "status": "success",
        "message": f"Đã kích hoạt quét tự động mỗi {config.interval_minutes} phút",
        "data": scheduler.get_status()
    }

@app.post("/api/scheduler/stop", summary="Dừng lập lịch quét tự động")
async def stop_scheduler():
    scheduler.stop()
    return {
        "status": "success",
        "message": "Đã dừng quét mạng tự động",
        "data": scheduler.get_status()
    }
    
# Phục vụ giao diện Frontend
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")