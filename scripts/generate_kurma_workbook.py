#!/usr/bin/env python3
"""
AstroOS — Pre-configure and generate the official Kurma Chakra & SBC Excel Template (.xlsx).

Usage:
    python scripts/generate_kurma_workbook.py [output_path]
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

# Add workspace root to sys.path
root_dir = Path(__file__).resolve().parents[1]
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from apps.api.services.excel_export_service import ExcelExportService


def main() -> None:
    output_path = Path(sys.argv[1]) if len(sys.argv) > 1 else root_dir / "docs" / "templates" / "AstroOS_Kurma_Display_Template.xlsx"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Generating AstroOS Kurma Chakra & SBC Workbook Template...")
    service = ExcelExportService()
    now_utc = datetime.now(timezone.utc)
    wb_bytes = service.generate_kurma_workbook_bytes(dt=now_utc, ayanamsa="lahiri")

    with open(output_path, "wb") as f:
        f.write(wb_bytes)

    print(f"[OK] Successfully generated template ({len(wb_bytes):,} bytes): {output_path}")


if __name__ == "__main__":
    main()
