
# tests/test_security_scorer.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scanner.security_scorer import evaluate_network_security

def test_security_scoring():
    mock_hosts = {
        "192.168.1.1": {
            "mac": "AA:BB:CC:DD:EE:FF",
            "vendor": "Router",
            "ports": [{"port": 80, "service": "HTTP"}]  # Trừ 5 điểm
        },
        "192.168.1.3": {
            "mac": "Unknown",
            "vendor": "Laptop",
            "ports": [
                {"port": 135, "service": "RPC"},       # Trừ 10 điểm
                {"port": 445, "service": "SMB"}        # Trừ 15 điểm
            ]
        }
    }
    
    result = evaluate_network_security(mock_hosts)
    # 100 - 5 (HTTP) - 10 (RPC) - 15 (SMB) = 70 điểm -> Hạng B
    assert result["score"] == 70
    assert result["grade"] == "B"
    assert result["total_issues"] == 3
    print("✅ Test Security Scorer: PASS (70/100 - Hạng B)")

if __name__ == "__main__":
    test_security_scoring()
