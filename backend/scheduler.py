# backend/scheduler.py

import asyncio
import datetime
from typing import Callable, Optional

class ScanScheduler:
    def __init__(self):
        self.is_running: bool = False
        self.interval_minutes: int = 30
        self.target: str = "192.168.1.1/24"
        self.last_run: Optional[str] = None
        self.next_run: Optional[str] = None
        self._task: Optional[asyncio.Task] = None

    def get_status(self) -> dict:
        return {
            "is_running": self.is_running,
            "interval_minutes": self.interval_minutes,
            "target": self.target,
            "last_run": self.last_run,
            "next_run": self.next_run
        }

    async def _worker_loop(self, scan_fn: Callable, run_immediately: bool = False):
        try:
            # 1. Chạy ngay phiên quét baseline nếu được yêu cầu
            if run_immediately:
                self.last_run = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                try:
                    await asyncio.to_thread(scan_fn, self.target)
                except Exception as exc:
                    print(f"[Scheduler Error] Phiên quét ban đầu thất bại: {exc}")

            # 2. Vòng lặp định kỳ theo chu kỳ
            while self.is_running:
                # Tính toán và cập nhật mốc thời gian quét tiếp theo
                now = datetime.datetime.now()
                next_time = now + datetime.timedelta(minutes=self.interval_minutes)
                self.next_run = next_time.strftime("%Y-%m-%d %H:%M:%S")

                # Chờ đến chu kỳ kế tiếp
                await asyncio.sleep(self.interval_minutes * 60)

                if not self.is_running:
                    break

                # Thực thi quét định kỳ
                self.last_run = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                try:
                    await asyncio.to_thread(scan_fn, self.target)
                except Exception as exc:
                    print(f"[Scheduler Error] Quét tự động thất bại: {exc}")

        except asyncio.CancelledError:
            # Thoát vòng lặp êm ái khi người dùng bấm Stop
            pass
        finally:
            self.is_running = False
            self.next_run = None

    def start(self, target: str, interval_minutes: int, scan_fn: Callable, run_immediately: bool = False):
        """Khởi động bộ lập lịch."""
        if self.is_running:
            self.stop()

        self.is_running = True
        self.target = target
        self.interval_minutes = max(1, interval_minutes)

        if not run_immediately:
            next_time = datetime.datetime.now() + datetime.timedelta(minutes=self.interval_minutes)
            self.next_run = next_time.strftime("%Y-%m-%d %H:%M:%S")

        # Đăng ký worker task vào Event Loop
        self._task = asyncio.create_task(self._worker_loop(scan_fn, run_immediately))

    def stop(self):
        """Dừng bộ lập lịch và hủy task ngầm."""
        self.is_running = False
        self.next_run = None
        if self._task and not self._task.done():
            self._task.cancel()
            self._task = None

scheduler = ScanScheduler()