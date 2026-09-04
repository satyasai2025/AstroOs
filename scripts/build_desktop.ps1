# ==============================================================================
# AstroOS Desktop App Build Script (Tauri Windows Target)
# ==============================================================================

Write-Host "===================================================================" -ForegroundColor Cyan
Write-Host " AstroOS Desktop Application Builder" -ForegroundColor Cyan
Write-Host " Target: Windows Native (.exe / NSIS Installer)" -ForegroundColor Cyan
Write-Host "===================================================================" -ForegroundColor Cyan

# Step 1: Check prerequisites
if (-not (Get-Command pnpm -ErrorAction SilentlyContinue)) {
    Write-Error "pnpm is not installed. Please install pnpm."
    exit 1
}

# Step 2: Build Web UI
Write-Host "[1/3] Building Web Workstation frontend..." -ForegroundColor Yellow
Set-Location -Path "apps/web"
pnpm run build
if ($LASTEXITCODE -ne 0) {
    Write-Error "Web build failed."
    Set-Location -Path "../.."
    exit 1
}
Set-Location -Path "../.."

# Step 3: Bundle Tauri App
Write-Host "[2/3] Bundling Tauri Native Desktop Binaries..." -ForegroundColor Yellow
Set-Location -Path "apps/desktop"
pnpm run build
if ($LASTEXITCODE -ne 0) {
    Write-Error "Desktop bundling failed."
    Set-Location -Path "../.."
    exit 1
}
Set-Location -Path "../.."

# Step 4: Completion Summary
Write-Host "[3/3] Build completed successfully!" -ForegroundColor Green
Write-Host "Generated binaries located in:" -ForegroundColor Green
Write-Host " -> apps/desktop/src-tauri/target/release/bundle/" -ForegroundColor Green
