const API_BASE = "http://127.0.0.1:8000/api";
let pollingTimer = null;
let schedulerPollTimer = null;

document.addEventListener("DOMContentLoaded", () => {
    loadHistory();
    loadDiff();
    initScheduler();
    checkInitialScanStatus();
});

// ================= 1. QUẢN LÝ QUÉT THỦ CÔNG & TIẾN ĐỘ =================

// Kích hoạt phiên quét mới thủ công
async function startScan() {
    const target = document.getElementById("target-input").value.trim();
    if (!target) return alert("Vui lòng nhập dải mạng!");

    const btn = document.getElementById("scan-btn");
    btn.disabled = true;

    try {
        const res = await fetch(`${API_BASE}/scan`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ target: target })
        });

        if (!res.ok) {
            const err = await res.json();
            alert(err.detail || "Lỗi khởi động quét");
            btn.disabled = false;
            return;
        }

        // Hiển thị thanh tiến độ và bắt đầu Polling
        document.getElementById("progress-container").classList.remove("hidden");
        startPolling();
    } catch (e) {
        alert("Không thể kết nối đến máy chủ Backend!");
        btn.disabled = false;
    }
}

// Kiểm tra trạng thái tiến trình quét (Polling mỗi 1.5s)
function startPolling() {
    if (pollingTimer) clearInterval(pollingTimer);

    pollingTimer = setInterval(async () => {
        try {
            const res = await fetch(`${API_BASE}/scan/status`);
            const data = await res.json();

            // Cập nhật giao diện thanh tiến độ
            document.getElementById("progress-step").innerText = data.step;
            document.getElementById("progress-percent").innerText = `${data.progress}%`;
            document.getElementById("progress-bar-fill").style.width = `${data.progress}%`;

            // Khi phiên quét hoàn tất
            if (!data.is_running && data.progress === 100) {
                clearInterval(pollingTimer);
                pollingTimer = null;
                document.getElementById("scan-btn").disabled = false;

                // Tải dữ liệu mới nhất
                if (data.last_scan_id) {
                    loadScanDetail(data.last_scan_id);
                }
                loadHistory();
                loadDiff();
                fetchSchedulerStatus(); // Đồng bộ lại thời gian lần quét kế tiếp
            }
        } catch (e) {
            console.error("Lỗi Polling trạng thái:", e);
        }
    }, 1500);
}

// Tự động bắt tiến trình quét nếu đã có phiên chạy ngầm từ trước (do Scheduler kích hoạt)
async function checkInitialScanStatus() {
    try {
        const res = await fetch(`${API_BASE}/scan/status`);
        const data = await res.json();
        if (data.is_running && !pollingTimer) {
            document.getElementById("progress-container").classList.remove("hidden");
            document.getElementById("scan-btn").disabled = true;
            startPolling();
        }
    } catch (e) {
        console.error("Lỗi kiểm tra trạng thái quét ban đầu:", e);
    }
}

// ================= 2. QUẢN LÝ LẬP LỊCH QUÉT TỰ ĐỘNG (SCHEDULER) =================

function initScheduler() {
    const toggle = document.getElementById("scheduler-toggle");
    const intervalInput = document.getElementById("scheduler-interval");

    if (!toggle || !intervalInput) return;

    // Lấy cấu hình hiện tại từ máy chủ
    fetchSchedulerStatus();

    // Lắng nghe sự kiện bật/tắt Toggle
    toggle.addEventListener("change", async (e) => {
        const isChecked = e.target.checked;
        const targetNet = document.getElementById("target-input")?.value.trim() || "192.168.1.1/24";
        const interval = parseInt(intervalInput.value, 10) || 30;

        if (isChecked) {
            try {
                const res = await fetch(`${API_BASE}/scheduler/start`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ target: targetNet, interval_minutes: interval })
                });

                if (!res.ok) {
                    const err = await res.json();
                    alert(err.detail || "Không thể kích hoạt lập lịch!");
                    e.target.checked = false;
                    return;
                }
            } catch (err) {
                alert("Lỗi kết nối khi bật scheduler!");
                e.target.checked = false;
                return;
            }
        } else {
            try {
                await fetch(`${API_BASE}/scheduler/stop`, { method: "POST" });
            } catch (err) {
                console.error("Lỗi khi dừng scheduler:", err);
            }
        }

        fetchSchedulerStatus();
    });

    // Cập nhật trạng thái scheduler định kỳ mỗi 15 giây
    if (!schedulerPollTimer) {
        schedulerPollTimer = setInterval(fetchSchedulerStatus, 15000);
    }
}

async function fetchSchedulerStatus() {
    const toggle = document.getElementById("scheduler-toggle");
    const intervalInput = document.getElementById("scheduler-interval");
    const statusLabel = document.getElementById("scheduler-status-label");
    const nextRunBox = document.getElementById("scheduler-next-run");
    const nextTimeLabel = document.getElementById("scheduler-next-time");

    if (!toggle || !statusLabel) return;

    try {
        const res = await fetch(`${API_BASE}/scheduler`);
        const data = await res.json();

        toggle.checked = data.is_running;
        intervalInput.value = data.interval_minutes;
        intervalInput.disabled = data.is_running;

        if (data.is_running) {
            statusLabel.textContent = "Đang bật";
            statusLabel.style.color = "#10b981";

            if (data.next_run) {
                nextRunBox.classList.remove("hidden");
                nextTimeLabel.textContent = data.next_run;
            } else {
                nextRunBox.classList.add("hidden");
            }

            // Nếu scheduler đang chạy phiên quét mà giao diện chưa polling thì kích hoạt ngay
            checkInitialScanStatus();
        } else {
            statusLabel.textContent = "Đang tắt";
            statusLabel.style.color = "var(--text-secondary, #94a3b8)";
            nextRunBox.classList.add("hidden");
        }
    } catch (e) {
        console.error("Lỗi đồng bộ trạng thái Scheduler:", e);
    }
}

// ================= 3. HIỂN THỊ DỮ LIỆU PHIÊN QUÉT & HOST =================

async function loadScanDetail(scanId) {
    try {
        const res = await fetch(`${API_BASE}/scans/${scanId}`);
        const data = await res.json();

        document.getElementById("scan-meta").innerText =
            `Scan #${data.id} (${data.target}) — Hoàn thành trong ${data.scan_time}s lúc ${data.created_at}`;

        const grid = document.getElementById("hosts-grid");
        grid.innerHTML = "";

        const hosts = Object.keys(data.hosts);
        if (hosts.length === 0) {
            grid.innerHTML = "<p style='color: var(--text-secondary)'>Không tìm thấy host nào Online.</p>";
            return;
        }

        hosts.forEach(ip => {
            const hostInfo = data.hosts[ip];
            const ports = hostInfo.ports || [];
            const mac = hostInfo.mac || "Unknown";
            const vendor = hostInfo.vendor || "Unknown Device";

            const card = document.createElement("div");
            card.className = "host-card";

            let portsHtml = "";
            if (ports.length === 0) {
                portsHtml = "<p style='font-size: 12px; color: var(--text-secondary); margin-top: 6px;'>Không có port mở (1-1000)</p>";
            } else {
                portsHtml = ports.map(p => {
                    const bannerHtml = p.banner ? `<span class="banner-text">↳ ${p.banner}</span>` : "";
                    return `
                        <div class="port-item">
                            <span class="port-pill">Port ${p.port} (${p.service})</span>
                            ${bannerHtml}
                        </div>
                    `;
                }).join("");
            }

            card.innerHTML = `
                <div class="host-ip">🖥️ ${ip}</div>
                <div class="host-meta">
                    <div><strong>MAC:</strong> <code>${mac}</code></div>
                    <div><span class="vendor-badge">${vendor}</span></div>
                </div>
                <div style="margin-top: 10px;">${portsHtml}</div>
            `;
            grid.appendChild(card);
        });

        // Nạp báo cáo an ninh cho phiên này
        loadSecurityAudit(scanId);

    } catch (e) {
        console.error("Lỗi lấy chi tiết scan:", e);
    }
}

// Tải lịch sử các phiên quét
async function loadHistory() {
    try {
        const res = await fetch(`${API_BASE}/scans`);
        const scans = await res.json();

        const tbody = document.getElementById("history-tbody");
        tbody.innerHTML = "";

        scans.forEach(s => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>#${s.id}</td>
                <td>${s.target}</td>
                <td>${s.scan_time}s</td>
                <td><strong style="color: var(--accent);">${s.total_hosts}</strong> máy</td>
                <td>${s.created_at}</td>
                <td><button onclick="loadScanDetail(${s.id})" style="padding: 4px 8px; font-size: 12px;">Xem</button></td>
            `;
            tbody.appendChild(tr);
        });

        // Nạp phiên quét mới nhất nếu có
        if (scans.length > 0) {
            loadScanDetail(scans[0].id);
        }
    } catch (e) {
        console.error("Lỗi nạp lịch sử:", e);
    }
}

// ================= 4. GIÁM SÁT BIẾN ĐỘNG (DIFFING) & ĐÁNH GIÁ AN NINH =================

async function loadDiff() {
    try {
        const res = await fetch(`${API_BASE}/diff`);
        const data = await res.json();
        const diffSection = document.getElementById("diff-section");
        const diffContent = document.getElementById("diff-content");

        if (!data.changes) {
            diffSection.classList.add("hidden");
            return;
        }

        diffSection.classList.remove("hidden");
        const changes = data.changes;

        if (changes.is_stable) {
            diffContent.innerHTML = `<p style="color: var(--success); font-size: 14px;">✓ Mạng ổn định: Không có thiết bị mới hoặc offline.</p>`;
            return;
        }

        let html = "";
        if (changes.new_hosts.length > 0) {
            html += `<p style="margin-bottom: 6px;"><span class="diff-tag diff-new">+ Mới kết nối:</span> ${changes.new_hosts.join(", ")}</p>`;
        }
        if (changes.offline_hosts.length > 0) {
            html += `<p><span class="diff-tag diff-offline">- Đã ngắt mạng:</span> ${changes.offline_hosts.join(", ")}</p>`;
        }

        diffContent.innerHTML = html;
    } catch (e) {
        console.error("Lỗi nạp Diff:", e);
    }
}

let securityAuditRequestSeq = 0;

async function loadSecurityAudit(scanId) {
    const requestSeq = ++securityAuditRequestSeq;
    const card = document.getElementById("security-card");
    const badge = document.getElementById("security-badge");
    const summary = document.getElementById("security-summary");
    const list = document.getElementById("security-findings-list");

    if (!card) return;

    try {
        const res = await fetch(`${API_BASE}/scans/${scanId}/security`);
        if (requestSeq !== securityAuditRequestSeq) return;
        if (!res.ok) {
            card.classList.add("hidden");
            return;
        }

        const data = await res.json();
        if (requestSeq !== securityAuditRequestSeq) return;
        const audit = data.audit;

        card.classList.remove("hidden");
        badge.className = `grade-${audit.grade}`;
        badge.innerText = `${audit.score}/100 (Hạng ${audit.grade})`;
        summary.innerText = `Trạng thái: ${audit.status} — Phát hiện ${audit.total_issues} rủi ro an ninh.`;

        if (audit.findings.length === 0) {
            list.innerHTML = "<p style='color: var(--success); font-size: 13px;'>Không phát hiện cổng dịch vụ có nguy cơ rủi ro cao.</p>";
            return;
        }

        list.innerHTML = audit.findings.map(f => `
            <div class="finding-item sev-${f.severity}">
                <div class="finding-title">
                    <span>[${f.severity}] <code>${f.ip}:${f.port}</code> — ${f.service}</span>
                    <span style="color: var(--danger); font-weight: bold;">-${f.penalty} điểm</span>
                </div>
                <div class="finding-desc">${f.description}</div>
                <div class="finding-remediation"><strong>Khắc phục:</strong> ${f.remediation}</div>
            </div>
        `).join("");

    } catch (e) {
        console.error("Lỗi khi tải dữ liệu Security Audit:", e);
        card.classList.add("hidden");
    }
}