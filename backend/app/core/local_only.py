"""Local runtime boundary for the application's standard Python socket operations.

This is an application safeguard, not a sandbox for malicious native extensions or
subprocesses. Feature modules must remain trusted and must not perform network I/O.
"""
import ipaddress
import socket
import sys

_installed = False

CONTENT_SECURITY_POLICY = (
    "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data:; font-src 'self'; connect-src 'self'; "
    "object-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'"
)

def is_loopback_host(host):
    if isinstance(host, bytes):
        try:
            host = host.decode("ascii")
        except UnicodeDecodeError:
            return False
    if not isinstance(host, str):
        return False
    if host.lower() == "localhost":
        return True
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return False
    mapped = getattr(address, "ipv4_mapped", None)
    return address.is_loopback or (mapped is not None and mapped.is_loopback)

def _require_local(host):
    if not is_loopback_host(host):
        raise PermissionError("DataMap Studio permits connections only within this computer.")

def _audit_network(event, args):
    if event in {"socket.connect", "socket.bind", "socket.sendto", "socket.sendmsg"}:
        sock, address = args[0], args[-1]
        if sock.family in (socket.AF_INET, socket.AF_INET6) and address is not None:
            if not isinstance(address, tuple) or not address:
                raise PermissionError("Only local IP socket addresses are supported.")
            _require_local(address[0])
    elif event in {"socket.getaddrinfo", "socket.gethostbyname", "socket.gethostbyaddr"}:
        _require_local(args[0])
    elif event == "socket.getnameinfo":
        _require_local(args[0][0])

def install_local_only_network_policy():
    global _installed
    if not _installed:
        sys.addaudithook(_audit_network)
        _installed = True
