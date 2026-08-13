"""
mDNS/Bonjour Session Discovery — RTCollab Phase IV (ADR-RTC-001, Milestone 1)

Advertises AstroOS collaboration sessions on the LAN as
"_astroos-collab._tcp.local." services and discovers sessions advertised
by other devices. Wraps the synchronous `zeroconf` API in a thread so it
composes cleanly with FastAPI's async request handlers.
"""

import asyncio
import socket
from dataclasses import dataclass
from typing import Dict, List, Optional

from zeroconf import ServiceBrowser, ServiceInfo, ServiceListener, Zeroconf

SERVICE_TYPE = "_astroos-collab._tcp.local."


@dataclass
class DiscoveredSession:
    session_id: str
    host_name: str
    address: str
    port: int


class _CollabListener(ServiceListener):
    """Maintains `registry` as a live view of sessions advertised on the LAN."""

    def __init__(self, registry: Dict[str, DiscoveredSession]):
        self._registry = registry

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        self._update(zc, type_, name)

    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        self._update(zc, type_, name)

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        self._registry.pop(name, None)

    def _update(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        if info is None or not info.addresses:
            return
        properties = {
            key.decode(): value.decode()
            for key, value in (info.properties or {}).items()
            if value is not None
        }
        self._registry[name] = DiscoveredSession(
            session_id=properties.get("session_id", ""),
            host_name=properties.get("host_name", "Unknown Host"),
            address=socket.inet_ntoa(info.addresses[0]),
            port=info.port or 0,
        )


class CollabDiscovery:
    """Advertises and discovers LAN-local RTCollab sessions via mDNS."""

    def __init__(self):
        self._zc: Optional[Zeroconf] = None
        self._browser: Optional[ServiceBrowser] = None
        self._advertised: Dict[str, ServiceInfo] = {}
        self._discovered: Dict[str, DiscoveredSession] = {}

    def _ensure_started(self) -> None:
        if self._zc is None:
            self._zc = Zeroconf()
            self._browser = ServiceBrowser(
                self._zc, SERVICE_TYPE, _CollabListener(self._discovered)
            )

    async def advertise(self, session_id: str, host_name: str, port: int) -> None:
        await asyncio.to_thread(self._advertise_sync, session_id, host_name, port)

    def _advertise_sync(self, session_id: str, host_name: str, port: int) -> None:
        self._ensure_started()
        assert self._zc is not None
        local_ip = socket.gethostbyname(socket.gethostname())
        info = ServiceInfo(
            SERVICE_TYPE,
            name=f"{session_id}.{SERVICE_TYPE}",
            addresses=[socket.inet_aton(local_ip)],
            port=port,
            properties={"session_id": session_id, "host_name": host_name},
        )
        existing = self._advertised.pop(session_id, None)
        if existing:
            self._zc.unregister_service(existing)
        self._zc.register_service(info)
        self._advertised[session_id] = info

    async def stop_advertising(self, session_id: str) -> None:
        await asyncio.to_thread(self._stop_advertising_sync, session_id)

    def _stop_advertising_sync(self, session_id: str) -> None:
        info = self._advertised.pop(session_id, None)
        if info and self._zc:
            self._zc.unregister_service(info)

    def list_discovered(self) -> List[DiscoveredSession]:
        self._ensure_started()
        return list(self._discovered.values())

    async def close(self) -> None:
        await asyncio.to_thread(self._close_sync)

    def _close_sync(self) -> None:
        if self._zc is None:
            return
        for info in list(self._advertised.values()):
            self._zc.unregister_service(info)
        self._advertised.clear()
        self._discovered.clear()
        self._zc.close()
        self._zc = None
        self._browser = None


# Process-wide singleton: one mDNS responder per running API instance.
discovery = CollabDiscovery()


def get_discovery() -> CollabDiscovery:
    return discovery
