"""
AstroOS Complete Backup Utility
Creates a clean, compressed zip backup in D:\\AstroOS_Backups\\
Excludes virtualenvs, node_modules, build artifacts, and pycache.
"""

import os
import zipfile
import datetime
from pathlib import Path

def create_backup():
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    src_dir = Path("c:/Users/rkmau/Downloads/ReplitplusClaude/AstroOS")
    dst_dir = Path("D:/AstroOS_Backups")
    dst_dir.mkdir(parents=True, exist_ok=True)
    
    zip_path = dst_dir / f"AstroOS_Full_Restoreable_Backup_{timestamp}.zip"
    
    excluded_dirs = {
        ".venv", "venv", "node_modules", ".next", ".git", 
        "__pycache__", ".pytest_cache", ".turbo", "dist", "build"
    }
    
    file_count = 0
    total_uncompressed = 0
    
    print(f"Creating backup at: {zip_path}")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
        for root, dirs, files in os.walk(src_dir):
            # Prune excluded directories in place
            dirs[:] = [d for d in dirs if d not in excluded_dirs]
            
            for file in files:
                if file.endswith(".pyc") or file.endswith(".pyo"):
                    continue
                file_path = Path(root) / file
                rel_path = file_path.relative_to(src_dir)
                try:
                    zipf.write(file_path, arcname=str(rel_path))
                    file_count += 1
                    total_uncompressed += file_path.stat().st_size
                except Exception as e:
                    print(f"Skipping {file_path}: {e}")

    zip_size_mb = zip_path.stat().st_size / (1024 * 1024)
    uncompressed_mb = total_uncompressed / (1024 * 1024)
    print(f"Backup SUCCESS: {file_count} files | {zip_size_mb:.2f} MB compressed (from {uncompressed_mb:.2f} MB)")
    return zip_path

if __name__ == "__main__":
    create_backup()
