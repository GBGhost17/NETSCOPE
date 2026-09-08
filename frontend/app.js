
const API_BASE = "http://127.0.0.1:8000/api";
let pollingTimer = null;

document.addEventListener("DOMContentLoaded", () => {
    loadHistory();
    loadDiff();
});

// 1. Kích hoạt phiên quét mới
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

        // Bật thanh tiến độ và bắt đầu Polling
        document.getElementById("progress-container").classList.remove("hidden");
        startPolling();
    } catch (e) {
        alert("Không thể kết nối đến máy chủ Backend!");
        btn.disabled = false;
    }
}

// 2. Kiểm tra trạng thái tiến trình quét (Polling mỗi 1.5s)
function startPolling() {
    pollingTimer = setInterval(async () => {
        try {
            const res = await fetch(`${API_BASE}/scan/status`);
            const data = await res.json();

            // Cập nhật UI thanh tiến độ
            document.getElementById("progress-step").innerText = data.step;
            document.getElementById("progress-percent").innerText = `${data.progress}%`;
            document.getElementById("progress-bar-fill").style.width = `${data.progress}%`;

            // Khi hoàn thành
            if (!data.is_running && data.progress === 100) {
                clearInterval(pollingTimer);
                document.getElementById("scan-btn").disabled = false;

                // Tải chi tiết phiên vừa quét xong
                if (data.last_scan_id) {
                    loadScanDetail(data.last_scan_id);
                }
                loadHistory();
                loadDiff();
            }
        } catch (e) {
            console.error("Lỗi Polling trạng thái:", e);
        }
    }, 1500);
}

// 3. Hiển thị chi tiết 1 phiên quét lên giao diện
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
    } catch (e) {
        console.error("Lỗi lấy chi tiết scan:", e);
    }
}

// 4. Tải danh sách lịch sử các phiên quét
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

        // Tự động nạp bản ghi mới nhất lên màn hình
        if (scans.length > 0) {
            loadScanDetail(scans[0].id);
        }
    } catch (e) {
        console.error("Lỗi nạp lịch sử:", e);
    }
}

// 5. Tải dữ liệu Diffing/Monitoring
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
