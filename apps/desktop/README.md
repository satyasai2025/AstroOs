# AstroOS Desktop App (Tauri v2)

A native desktop wrapper for the AstroOS Vedic Astrology Research Platform. Built with [Tauri v2](https://v2.tauri.app/), the desktop app wraps the AstroOS Next.js web frontend and automatically manages the FastAPI backend as a sidecar process.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                Tauri v2 Shell (Rust)                │
│  ┌──────────────────────────────────────────────┐   │
│  │  System Tray │ Window Management │ IPC API   │   │
│  └──────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────┐   │
│  │  React Shell (Vite + TypeScript)             │   │
│  │  ┌────────────────────────────────────────┐  │   │
│  │  │  Next.js Frontend (iframe)             │  │   │
│  │  │  Running at localhost:3000             │  │   │
│  │  │  App Router, TailwindCSS, D3.js        │  │   │
│  │  └────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────┐   │
│  │  FastAPI Backend (Sidecar Process)           │   │
│  │  Port 8000 · Health: /api/healthz            │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

The desktop app consists of three layers:
1. **Tauri Rust shell** (`src-tauri/`) — manages the FastAPI process lifecycle, system tray, window, and IPC bridge.
2. **React shell** (`src/`) — minimal UI that monitors API health and embeds the Next.js frontend in a webview.
3. **FastAPI sidecar** — spawned automatically on launch, terminates on exit.

## Prerequisites

| Tool | Version | Notes |
|------|---------|-------|
| Rust | 1.77+ | `rustc --version` — install via [rustup](https://rustup.rs/) |
| Node.js | 20+ | `node --version` |
| pnpm | 9+ | `npm install -g pnpm` |
| Python | 3.11+ | `python --version` — for the FastAPI backend |
| Tauri CLI | ^2.0.0 | Installed via pnpm (see below) |
| WebKit2GTK | (Linux only) | `sudo apt install libwebkit2gtk-4.1-dev` |

Additional Linux dependencies:
```bash
sudo apt install build-essential libssl-dev libgtk-3-dev \
  libayatana-appindicator3-dev librsvg2-dev
```

## Getting Started

### 1. Install dependencies

```bash
# From the project root, install all workspace dependencies
pnpm install

# Install Python dependencies
pip install -r apps/api/requirements.txt
```

### 2. Start the API server

The desktop app expects the AstroOS API to be running. For development, start it in a separate terminal:

```bash
cd apps/api
PYTHONPATH=. uvicorn apps.api.main:app --host 127.0.0.1 --port 8000 --reload
```

Verify it's running:
```bash
curl http://127.0.0.1:8000/api/healthz
```

### 3. Start the Next.js frontend (development)

In a second terminal:
```bash
cd apps/web
pnpm dev
```

The frontend will be available at `http://localhost:3000`.

### 4. Run the desktop app in development mode

In a third terminal:
```bash
cd apps/desktop
pnpm tauri dev
```

This compiles the Rust backend, starts the Vite dev server, and opens the Tauri window. The desktop shell will auto-detect the API health (at `localhost:8000`) and load the Next.js frontend in an iframe.

> **Note:** You can also have Tauri's Rust backend auto-start the API. See `lib.rs` — the `start_api_server` command is called automatically in the `setup` hook, and the Tauri tray menu provides start/stop/restart controls.

## Build for Production

### Step 1: Build the Next.js frontend

For a self-contained desktop build, the Next.js app must be exported as static files. Create a file `apps/web/next.export.config.ts`:

```ts
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "export",
  distDir: "out",
  images: { unoptimized: true },
};

export default nextConfig;
```

Then build:
```bash
cd apps/web
NEXT_CONFIG=next.export.config.ts pnpm next build
# or copy the config temporarily:
cp next.config.ts next.config.ts.bak
cp next.export.config.ts next.config.ts
pnpm build
mv next.config.ts.bak next.config.ts
```

The static export will be at `apps/web/out/`.

> Alternatively, update `next.config.ts` to conditionally use `output: "export"` based on an environment variable (e.g., `DESKTOP_BUILD=true`).

### Step 2: Build the Tauri app

```bash
cd apps/desktop

# Build in release mode (creates installer)
pnpm tauri build
```

The installer will be at:
- **Windows**: `src-tauri/target/release/bundle/msi/` or `nsis/`
- **macOS**: `src-tauri/target/release/bundle/dmg/`
- **Linux**: `src-tauri/target/release/bundle/deb/`

### Step 3: (Optional) Bundle the API as a sidecar

For a fully self-contained build (no system Python dependency), compile the API into a standalone executable using PyInstaller:

```bash
pip install pyinstaller
cd apps/api
pyinstaller --onefile --name astroos-api apps/api/main.py
```

Copy the resulting binary to `apps/desktop/src-tauri/binaries/` with the proper naming convention (`astroos-api-{target-triple}[.exe]`) and add it to `bundle.externalBin` in `tauri.conf.json`.

## Project Structure

```
apps/desktop/
├── index.html                      # Vite HTML entry point
├── package.json                    # Node dependencies and scripts
├── tsconfig.json                   # TypeScript configuration
├── tsconfig.node.json              # TypeScript config for Vite/Node
├── vite.config.ts                  # Vite bundler configuration
├── src/
│   ├── main.tsx                    # React entry point
│   ├── App.tsx                     # Main shell component (health, iframe)
│   └── vite-env.d.ts              # Vite type declarations
├── src-tauri/
│   ├── Cargo.toml                  # Rust dependencies
│   ├── build.rs                    # Tauri build script
│   ├── tauri.conf.json             # Tauri app configuration
│   ├── capabilities/
│   │   └── default.json           # Permission capabilities
│   ├── icons/                      # App icons (placeholder)
│   └── src/
│       ├── main.rs                 # Rust entry point (windows_subsystem)
│       └── lib.rs                  # Core: process mgmt, tray, commands
└── README.md                       # This file
```

## Key Rust Commands (IPC)

| Command | Description |
|---------|-------------|
| `start_api_server` | Start the FastAPI backend process |
| `stop_api_server` | Gracefully stop the API process |
| `restart_api_server` | Restart the API process |
| `check_api_health` | Returns `true` if the API health endpoint responds |
| `get_api_health` | Returns the full health JSON payload |
| `get_api_port` | Returns the configured API port (default 8000) |

These commands are callable from the React frontend via `@tauri-apps/api/core`'s `invoke()`.

## Development Tips

- **Hot reload**: The Vite dev server supports HMR for the desktop shell UI. Changes to `src/` are reflected instantly.
- **Rust changes**: The Tauri Rust code must be recompiled (`pnpm tauri dev`).
- **API changes**: The FastAPI `--reload` flag provides hot reload for backend changes.
- **Logs**: API stdout/stderr is piped through the Rust process and printed to the terminal running `tauri dev`.
- **Tray**: Right-click the system tray icon to show/hide the window or quit.

## Troubleshooting

| Problem | Likely Cause | Fix |
|---------|-------------|-----|
| `WebKit2GTK not found` | Missing Linux deps | `sudo apt install libwebkit2gtk-4.1-dev` |
| `Python not found` | Python not in PATH | Install Python 3.11+ and ensure it's on PATH |
| `ModuleNotFoundError: apps.api` | Wrong working directory | Run from project root, or set `API_WORKING_DIR` |
| `Connection refused on 127.0.0.1:8000` | API not started | Start the API manually, or wait for auto-start |
| Blank iframe | CSP blocking the load | Check `app.security.csp` in tauri.conf.json |
