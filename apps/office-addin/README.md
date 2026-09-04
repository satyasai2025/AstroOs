# AstroOS Office.js Add-In & Excel Integration

This module bridges AstroOS's real-time computational astrology engine with Microsoft Excel via Office.js and pre-configured `.xlsx` templates.

---

## Key Features

1. **Structured ListObject Integration (`tblVedhaMap`)**:
   - Manages the 112-pada Sarvatobhadra Chakra (SBC) cross-reference table.
   - Preserves table column definitions and supports resilient `INDEX(MATCH())` & `XLOOKUP` formula bindings.

2. **DELETE-then-APPEND Row Lifecycle**:
   - Purges stale data rows before inserting fresh batches, preventing ghost rows and dangling `#N/A` references.

3. **Batched 2D Array Updates**:
   - Assigns 9-directional Kurma Chakra vulnerability matrices in a single `range.values = [...]` call, avoiding slow per-cell RPC round-trips.

4. **Post-Write Error-Cell Validation Scan**:
   - Audits calculated cells on `Kurma_Display` for `#N/A`, `#REF!`, `#VALUE!`, `#NAME?`, or empty keys after every sync and reports diagnostics in the taskpane.

5. **Idempotency**:
   - Safe to re-run repeatedly without duplicate rows or table corruption.

---

## Files

- `manifest.xml`: Office.js manifest for Excel Desktop, Web, and Mac.
- `taskpane.html`: Taskpane HTML interface.
- `taskpane.ts` / `taskpane.js`: Office.js Excel transaction controller with error scanner.
- `package.json`: Add-in dependencies and scripts.

---

## How to Run & Sideload in Excel

### 1. Start AstroOS API
Ensure the AstroOS FastAPI backend is running:
```bash
python -m uvicorn apps.api.main:app --port 8000 --reload
```

### 2. Generate the Template Workbook
Generate the pre-configured Excel template:
```bash
python scripts/generate_kurma_workbook.py
```
Open the generated file: `docs/templates/AstroOS_Kurma_Display_Template.xlsx` in Excel.

### 3. Serve the Taskpane
From `apps/office-addin`:
```bash
npx serve -l 3000 .
```

### 4. Sideload Manifest into Excel
In Excel:
1. Go to **Insert** > **Add-ins** > **My Add-ins** > **Upload My Add-in**.
2. Select `apps/office-addin/manifest.xml`.
3. Open the **AstroOS** tab on the ribbon and click **Open Console**.
4. Click **Sync Kurma & SBC Tables** to update.
