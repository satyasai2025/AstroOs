# Desktop Build Guide (Platform-Specific)

This guide covers building the AstroOS Tauri desktop application on Windows, macOS, and Linux.

---

## Table of Contents

1. [Common Prerequisites](#common-prerequisites)
2. [Windows Build Guide](#windows-build-guide)
3. [macOS Build Guide](#macos-build-guide)
4. [Linux Build Guide](#linux-build-guide)
5. [Cross-Compilation Notes](#cross-compilation-notes)
6. [Troubleshooting](#troubleshooting)

---

## Common Prerequisites

All platforms require these tools regardless of OS:

| Tool | Version | Install |
|------|---------|---------|
| Rust | 1.77+ | `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh` |
| Node.js | 20+ | [nodejs.org](https://nodejs.org/) or `nvm install 20` |
| pnpm | 9+ | `npm install -g pnpm` |
| Python | 3.11+ | [python.org](https://python.org/) |
| Tauri CLI | ^2.0 | `pnpm add -g @tauri-apps/cli` or workspace-local via `pnpm tauri` |

Verify your environment:

```bash
rustc --version         # rustc 1.77+
node --version          # v20+
pnpm --version          # 9+
python --version        # Python 3.11+
```

---

## Windows Build Guide

### Additional Requirements

- **Microsoft Visual Studio Build Tools** (or Visual Studio 2022 with "Desktop development with C++" workload)
  - Download: https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022
  - Required components: MSVC v143, Windows SDK, C++ CMake tools
- **WebView2** — preinstalled on Windows 10+ (Version 1803+). Verify in `Settings > Apps > Microsoft Edge WebView2 Runtime`.
- Install via `pnpm` / `pip` as usual — no extra Linux-like system packages.

### Build Steps

```powershell
# 1. Install workspace dependencies
cd C:\AstroOS
pnpm install

# 2. Install Python API dependencies
pip install -r apps/api/requirements.txt

# 3. Build the Next.js frontend (see main README for export config)
cd apps/web
pnpm build
cd ../..

# 4. Build the desktop app for release
cd apps/desktop
pnpm tauri build
```

### Output

The installer will be created at:
```
apps/desktop/src-tauri/target/release/bundle/msi/AstroOS_2.0.0_x64_en-US.msi
apps/desktop/src-tauri/target/release/bundle/nsis/AstroOS_2.0.0_x64-setup.exe
```

The NSIS installer is recommended for end users (signed, lighter). The MSI is better for enterprise deployment.

### Known Issues

- **Antivirus false positives**: Some antivirus software may flag the bundled NSIS installer. Submit a false-positive report to the vendor.
- **Long paths**: Ensure `git config --system core.longpaths true` if the build fails with path-length errors.
- **Firewall prompt**: The first launch may trigger a Windows Defender firewall prompt for the API process. Allow localhost access.

---

## macOS Build Guide

### Additional Requirements

- **Xcode Command Line Tools** (or full Xcode from the App Store)
  ```bash
  xcode-select --install
  ```
- No additional system packages needed — macOS includes all required libraries.

### Developer ID Signing (for distribution)

For distribution outside the Mac App Store, sign the app with an Apple Developer ID:

```bash
# Generate a certificate signing request and obtain a "Developer ID Application"
# certificate from developer.apple.com, then:
security find-identity -v -p basic                    # List available identities
export APPLE_SIGNING_IDENTITY="Developer ID Application: Your Name (TEAMID)"
```

Add to `tauri.conf.json`:
```json
{
  "bundle": {
    "macOS": {
      "signingIdentity": "$APPLE_SIGNING_IDENTITY",
      "entitlements": "entitlements.plist"
    }
  }
}
```

Create `apps/desktop/src-tauri/entitlements.plist`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>com.apple.security.cs.allow-unsigned-executable-memory</key>
    <true/>
    <key>com.apple.security.network.client</key>
    <true/>
    <key>com.apple.security.network.server</key>
    <true/>
</dict>
</plist>
```

> **Note**: Notarization is required for macOS 10.15+ to avoid Gatekeeper warnings. After building, run:
> ```bash
> xcrun notarytool submit apps/desktop/src-tauri/target/release/bundle/dmg/AstroOS.dmg \
>   --apple-id your@email.com --team-id TEAMID --password @keychain:AC_PASSWORD \
>   --wait
> xcrun stapler staple apps/desktop/src-tauri/target/release/bundle/dmg/AstroOS.dmg
> ```

### Build Steps

```bash
# 1. Install workspace dependencies
cd /path/to/AstroOS
pnpm install
pip install -r apps/api/requirements.txt

# 2. Build Next.js and desktop
cd apps/web && pnpm build && cd ../..
cd apps/desktop && pnpm tauri build
```

### Output

```
apps/desktop/src-tauri/target/release/bundle/dmg/AstroOS.dmg
apps/desktop/src-tauri/target/release/bundle/macos/AstroOS.app
```

### Universal Binary (Apple Silicon + Intel)

For a universal binary that runs natively on both arm64 and x86_64:

```bash
# Build for both architectures
rustup target add aarch64-apple-darwin x86_64-apple-darwin

# Tauri build on Apple Silicon auto-targets arm64.
# For universal binary, build twice and merge:
cd apps/desktop
pnpm tauri build --target aarch64-apple-darwin
pnpm tauri build --target x86_64-apple-darwin

# Use lipo to create a universal binary from the two app bundles:
lipo -create \
  src-tauri/target/aarch64-apple-darwin/release/astroos-desktop \
  src-tauri/target/x86_64-apple-darwin/release/astroos-desktop \
  -output astroos-desktop-universal
```

---

## Linux Build Guide

### Additional Requirements

```bash
# Debian / Ubuntu / Pop!_OS / Linux Mint
sudo apt update
sudo apt install build-essential curl wget file libssl-dev libgtk-3-dev \
  libwebkit2gtk-4.1-dev libayatana-appindicator3-dev librsvg2-dev \
  libjavascriptcoregtk-4.1-dev libsoup-3.0-dev

# Fedora
sudo dnf groupinstall "C Development Tools and Libraries"
sudo dnf install openssl-devel gtk3-devel webkit2gtk4.1-devel \
  libappindicator-gtk3-devel librsvg2-devel

# Arch Linux
sudo pacman -S base-devel webkit2gtk-4.1 libappindicator-gtk3 \
  librsvg libsoup3

# openSUSE
sudo zypper install -t pattern devel_basis
sudo zypper install libopenssl-devel gtk3-devel webkit2gtk-4_1-devel \
  libappindicator3-devel librsvg-devel
```

> **Important for Ubuntu 22.04 users**: The default repositories may have an older WebKit2GTK. Add the Tauri team's PPA:
> ```bash
> sudo add-apt-repository ppa:okirby/tauri-focal-backports
> sudo apt update
> sudo apt install libwebkit2gtk-4.1-dev
> ```

### Build Steps

```bash
# 1. Install workspace dependencies
cd /path/to/AstroOS
pnpm install
pip install -r apps/api/requirements.txt

# 2. Build Next.js and desktop
cd apps/web && pnpm build && cd ../..
cd apps/desktop && pnpm tauri build
```

### Output

```
apps/desktop/src-tauri/target/release/bundle/deb/astroos-desktop_2.0.0_amd64.deb
apps/desktop/src-tauri/target/release/bundle/appimage/astroos-desktop_2.0.0_amd64.AppImage
```

### Distribution Formats

| Format | Recommended For | Notes |
|--------|----------------|-------|
| `.deb` | Debian/Ubuntu-based distros | Installs system-wide |
| `.AppImage` | All distros (portable) | No install needed, double-click to run |
| `.rpm` | Fedora/RHEL-based | Enable `rpm` bundle target in tauri.conf.json |

### AppImage Notes

- The AppImage requires `fuse` or `fuse3`:
  ```bash
  sudo apt install fuse3
  ```
- The environment variable `APPIMAGE_EXTRACT_AND_RUN=1` helps on some systems:
  ```bash
  APPIMAGE_EXTRACT_AND_RUN=1 ./AstroOS_2.0.0_amd64.AppImage
  ```

---

## Cross-Compilation Notes

### Windows → Linux/macOS (not recommended)

Cross-compiling Tauri from Windows to non-Windows targets is not supported. Use native builds or CI runners (GitHub Actions, GitLab CI).

### macOS → Windows (via MinGW)

Cross-compilation from macOS to Windows is possible but complex:

```bash
# Install MinGW toolchain
brew install mingw-w64

# Add Windows target
rustup target add x86_64-pc-windows-gnu

# Build with MinGW
cd apps/desktop
cargo build --target x86_64-pc-windows-gnu --release
```

This approach has limitations with code signing and the MSI/NSIS bundler. It is not recommended for release builds.

### Linux → Windows (via MinGW)

```bash
sudo apt install gcc-mingw-w64
rustup target add x86_64-pc-windows-gnu
cd apps/desktop
cargo build --target x86_64-pc-windows-gnu --release
```

Again, the MSI/NSIS bundlers require Windows-native tooling. Use CI with Windows runners for full installer builds.

---

## CI/CD (GitHub Actions)

Example workflow excerpt for building the desktop app on all three platforms:

```yaml
jobs:
  build:
    strategy:
      matrix:
        os: [ubuntu-22.04, windows-2022, macos-14]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "20" }
      - uses: actions-rust-lang/setup-rust-toolchain@v1
      - name: Install Linux deps
        if: runner.os == 'Linux'
        run: sudo apt install libwebkit2gtk-4.1-dev libappindicator3-dev
      - run: pnpm install
      - run: pip install -r apps/api/requirements.txt
      - run: cd apps/web && pnpm build
      - run: cd apps/desktop && pnpm tauri build
```

---

## Troubleshooting

### Build Failures

| Symptom | Platform | Fix |
|---------|----------|-----|
| `linker 'cc' not found` | Linux | `sudo apt install build-essential` |
| `WebKit2GTK not found` | Linux | `sudo apt install libwebkit2gtk-4.1-dev` |
| `ATK library not found` | Linux | `sudo apt install libatk1.0-dev` |
| `MSBuild error MSB4019` | Windows | Install Visual Studio Build Tools with "Desktop C++" workload |
| `No such file or directory: 'python'` | All | Ensure Python is on PATH (try `python3` instead) |
| `ModuleNotFoundError: apps.api` | All | Run build from project root, or set `API_WORKING_DIR` |
| `error: failed to run custom build command for 'tauri-plugin-shell'` | All | Update Rust: `rustup update` |

### Runtime Issues

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| "API did not start" screen | Python/uvicorn not available | Start API manually: `PYTHONPATH=. uvicorn apps.api.main:app --port 8000` |
| Blank white window | Frontend build missing | Ensure Next.js is built (see main README) |
| Tray icon not appearing | Linux: no AppIndicator | Install `libayatana-appindicator3-dev` and rebuild |
| Cannot connect to API (Windows) | Firewall blocking | Allow `uvicorn` or `python` through Windows Firewall for localhost |
| macOS: "app is damaged" | Not notarized | Run `sudo xattr -rd com.apple.quarantine /Applications/AstroOS.app` |
| High CPU usage | API busy with computation | Check `localhost:8000/api/healthz` — ephemeris initialization is CPU-intensive on first call |

### Debug Build

For diagnostic builds with verbose logging:

```bash
cd apps/desktop
pnpm tauri dev 2>&1 | tee build.log
```

Pass `RUST_LOG=debug` for additional Rust logs:

```bash
RUST_LOG=debug pnpm tauri dev
```

---

## Version Compatibility

| Desktop App | AstroOS API | Tauri | Rust |
|-------------|-------------|-------|------|
| 2.0.0 | 2.x (v2.3.0 Lakshmi) | 2.x | 1.77+ |

The desktop app is tied to the AstroOS API version. Always build with the matching API version from the repository.
