"""Native desktop mode requires no IP sockets, including localhost."""
import socket
import sys
_installed = False

def _deny_network(event, args):
    if event == "socket.__new__" and args[1] in (socket.AF_INET, socket.AF_INET6):
        raise PermissionError("DataMap Studio desktop does not use network sockets.")
    if event in {"socket.getaddrinfo", "socket.gethostbyname", "socket.gethostbyaddr", "socket.getnameinfo"}:
        raise PermissionError("DataMap Studio desktop does not use hostname resolution.")

def install_no_network_policy():
    global _installed
    if not _installed:
        sys.addaudithook(_deny_network)
        _installed = True
