import socket
import sys
import pytest
from app.core.local_only import install_local_only_network_policy, is_loopback_host
from test_api import test_complete_workflow as run_complete_workflow

@pytest.mark.parametrize("host", ["127.0.0.1", "::1", "localhost", "::ffff:127.0.0.1"])
def test_loopback_hosts(host):
    assert is_loopback_host(host)

@pytest.mark.parametrize("host", ["0.0.0.0", "192.168.1.2", "8.8.8.8", "example.com", "localhost.example.com"])
def test_nonlocal_hosts(host):
    assert not is_loopback_host(host)

def test_external_connections_and_dns_are_blocked_before_io():
    install_local_only_network_policy()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        with pytest.raises(PermissionError, match="only within"):
            sock.connect(("192.0.2.1", 443))
        with pytest.raises(PermissionError, match="only within"):
            sock.bind(("0.0.0.0", 0))
        # An audit event exercises the local allowance without opening any port.
        sys.audit("socket.connect", sock, ("127.0.0.1", 8000))
    with pytest.raises(PermissionError, match="only within"):
        socket.getaddrinfo("example.com", 443)

def test_docs_and_browser_policy_are_self_contained(client):
    response = client.get("/docs")
    assert response.status_code == 200
    assert "Local API reference" in response.text
    assert 'href="/openapi.json"' in response.text
    assert "cdn." not in response.text
    assert "<script" not in response.text
    assert "https://" not in response.text
    assert "connect-src 'self'" in response.headers["content-security-policy"]
    assert "script-src 'self'" in response.headers["content-security-policy"]
    assert client.app.docs_url is None
    assert client.app.redoc_url is None
    assert client.get("/openapi.json").status_code == 200

def test_full_processing_works_with_network_policy_active(client, workbooks):
    install_local_only_network_policy()
    run_complete_workflow(client, workbooks)
