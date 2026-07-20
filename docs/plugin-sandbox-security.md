# Plugin Sandbox Security Audit — AstroOS v2.3.0

## Threat Model

| Threat | Severity | Mitigation |
|--------|----------|------------|
| Plugin reads host filesystem | High | Sandbox blocks filesystem access by default |
| Plugin makes network calls | Medium | Network blocked by default; opt-in via manifest |
| Plugin consumes all CPU | Medium | CPU limit per sandbox (configurable) |
| Plugin exhausts memory | Medium | Memory limit per sandbox (configurable) |
| Plugin persists malicious code | Low | Plugin stored in ~/.astroos/plugins; no auto-exec |
| Plugin steals API keys | Low | Sandbox has no access to host env vars |

## Sandbox Architecture

```
┌─────────────────────────────────────────┐
│  Host Process (AstroOS API)             │
│  ┌───────────────────────────────────┐  │
│  │  Sandbox (subprocess)             │  │
│  │  - CPU limit: 1 core              │  │
│  │  - Memory limit: 128 MB           │  │
│  │  - Network: BLOCKED by default    │  │
│  │  - filesystem: READ-ONLY (plugin) │  │
│  │  - Input: JSON via stdin          │  │
│  │  - Output: JSON via stdout        │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

## Implementation

The sandbox uses:
- **Linux:** `subprocess` with `prlimit` for CPU/memory, seccomp for network (via `python-seccomp` if available)
- **macOS:** `subprocess` with `resource.setrlimit`
- **Windows:** `subprocess` with job objects (CPU limit only; memory limit uses `psutil` if available)

## Audit Checklist

- [ ] Verify `subprocess` sandbox correctly applies CPU limits
- [ ] Verify `subprocess` sandbox correctly applies memory limits
- [ ] Verify network access is blocked for plugins with `network: false`
- [ ] Verify plugin cannot read files outside its installation directory
- [ ] Verify plugin cannot write to the host filesystem
- [ ] Verify plugin stdin/stdout channels cannot be subverted
- [ ] Verify plugin timeout kills the process after N seconds
- [ ] Verify malicious plugin cannot persist across app restarts
