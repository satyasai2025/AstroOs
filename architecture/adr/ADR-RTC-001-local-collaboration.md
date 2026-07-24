# ADR-RTC-001 – Local-Network Real-Time Collaboration (RTCollab)

**Status:** Proposed (Phase IV)  
**Date:** 2026-07-20  

## Context
- AstroOS is a **local-first, single-user** platform (per `CLAUDE_START_HERE.md` and Phase III audit).  
- “Real‑Time Collaboration” is deferred from Phase III to Phase IV but remains a **core future capability**.  
- Collaboration must operate **without cloud services**, relying only on devices on the same LAN.  
- Must preserve the existing local‑first guarantees: data never leaves the user’s device/network, no external accounts, no server farms.

## Decision
Implement a **peer‑to‑peer WebSocket sync layer** with a **local session coordinator**:

| Component | Responsibility |
|-----------|----------------|
| **Session Coordinator** | Discovers local devices via mDNS/Bonjour; acts as initial socket hub. |
| **WebSocket Transport** | Low‑latency, binary‑frame messages over TLS‑disabled WS (LAN trust). |
| **Sync Protocol** | Operational Transform (OT) with version vectors for conflict resolution. |
| **Message Types** | `chart_update`, `yoga_detect`, `mq_message`, `presence`. |
| **Security** | End‑to‑end AES‑256‑GCM encryption; sandbox per‑device CPU quota enforced by `WorkerPool`. |
| **NAT Traversal** | Optional STUN/TURN fallback; disabled by default (LAN‑only mode). |
| **Fallback Strategy** | If соединение lost, queue changes locally; re‑sync when reconnect. |

## Consequences
### ✅ Positive
- **True local‑first**: No data ever leaves the LAN boundary.  
- **Offline‑first**: Users can work offline; changes sync later.  
- **Extensible**: Protocol can be layered with voice/video in Phase V.  
- **Security**: Encryption + sandbox limits protect against rogue clients.  

### ⚠️ Trade‑offs
- **No cross‑internet collaboration** until Phase V introduces NAT‑traversal modules.  
- **More complex UI** needed for device discovery and session management.  
- **Potential race conditions** in OT must be rigorously tested.  
- **Performance impact** on low‑spec devices (CPU quota enforcement required).  

## Alternatives Considered
| Alternative | Why Rejected |
|-------------|--------------|
| Centralized cloud relay | Violates local‑first mandate. |
| Pure multicast DNS without coordinator | No reliable message ordering, difficult to handle conflicts. |
| Full OT framework from external lib | Overkill; we can implement a lightweight OT tailored to chart / yoga updates. |
| Browser‑only WebRTC | Limited to browsers; mobile apps need native WebSocket implementation. |

## Implementation Milestones
1. **Session Discovery** – mDNS broadcast of “astroos‑session”.  
2. **WebSocket Handshake** – TLS‑free WS with per‑device auth token.  
3. **OT Engine** – Version‑vector conflict resolution for chart updates.  
4. **Sandbox Integration** – Apply `WorkerPool` CPU caps per session.  
5. **UI Hooks** – Add “Connect Peer” button in Web UI and React‑Native mobile.  
6. **Testing** – Simulate LAN topologies (1‑1, 1‑many, lossy links).  

## Follow‑up ADRs
- `ADR-RTC-002-multi-device-sync-protocol` (OT details)  
- `ADR-RTC-003-sandbox‑quota‑enforcement`  
- `ADR-RTC-004‑fallback‑strategies`  

---  

*Prepared by:* Architecture Lead (you)  
*Reviewed by:* Backend Lead, Frontend Lead, QA Lead  
*Target Approval:* Product Owner (you)  

---  

*This ADR will be merged into `architecture/adr/` upon PO sign‑off and serves as the design foundation for the Phase IV RTCollab implementation.*