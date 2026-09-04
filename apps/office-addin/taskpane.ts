/**
 * AstroOS — Office.js Taskpane Controller for Excel
 * 
 * Implements:
 * 1. Batched 2D Array Range Updates (single context.sync per section)
 * 2. DELETE-then-APPEND ListObject Lifecycle on tblVedhaMap
 * 3. Post-Write Error-Cell Validation Scan (#N/A, #REF!, #VALUE!, #NAME?)
 * 4. Idempotent Re-execution Guarantee
 */

/* global Office, Excel */

interface VedhaRow {
  pada112: number;
  position: string;
  left: string;
  front: string;
  right: string;
}

interface VedhaResponse {
  count: number;
  headers: string[];
  rows: VedhaRow[];
}

interface KurmaDisplayPayload {
  evaluated_at: string;
  summary: string;
  highest_risk_directions: string[];
  summary_range: string;
  summary_values: (string | number)[][];
}

class AstroOSOfficeController {
  private logElement: HTMLElement | null = null;
  private badgeElement: HTMLElement | null = null;
  private syncButton: HTMLButtonElement | null = null;
  private auditButton: HTMLButtonElement | null = null;

  public init(): void {
    this.logElement = document.getElementById("logOutput");
    this.badgeElement = document.getElementById("auditBadge");
    this.syncButton = document.getElementById("syncBtn") as HTMLButtonElement;
    this.auditButton = document.getElementById("auditBtn") as HTMLButtonElement;

    // Set default target date to current UTC
    const dateInput = document.getElementById("targetDate") as HTMLInputElement;
    if (dateInput) {
      const now = new Date();
      now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
      dateInput.value = now.toISOString().slice(0, 16);
    }

    if (this.syncButton) {
      this.syncButton.addEventListener("click", () => this.handleSync());
    }

    if (this.auditButton) {
      this.auditButton.addEventListener("click", () => this.handleAuditOnly());
    }

    this.log("AstroOS Office.js Controller initialized.", "info");
  }

  private getApiBase(): string {
    const input = document.getElementById("apiUrl") as HTMLInputElement;
    return (input?.value || "http://localhost:8000").replace(/\/$/, "");
  }

  private getTargetDateISO(): string {
    const input = document.getElementById("targetDate") as HTMLInputElement;
    if (!input?.value) return new Date().toISOString();
    return new Date(input.value).toISOString();
  }

  private getAyanamsa(): string {
    const select = document.getElementById("ayanamsaSelect") as HTMLSelectElement;
    return select?.value || "lahiri";
  }

  public log(msg: string, level: "info" | "success" | "warn" | "error" = "info"): void {
    if (!this.logElement) return;
    const time = new Date().toLocaleTimeString();
    const line = `[${time}] ${msg}\n`;
    const span = document.createElement("span");
    span.className = `log-${level}`;
    span.textContent = line;
    this.logElement.appendChild(span);
    this.logElement.scrollTop = this.logElement.scrollHeight;
  }

  private setBadge(text: string, isOk: boolean): void {
    if (!this.badgeElement) return;
    this.badgeElement.textContent = text;
    this.badgeElement.className = `badge ${isOk ? "badge-ok" : "badge-error"}`;
  }

  /**
   * Main synchronization routine
   */
  public async handleSync(): Promise<void> {
    if (this.syncButton) this.syncButton.disabled = true;
    this.setBadge("SYNCING...", true);

    try {
      this.log("Starting full Kurma & SBC synchronization...", "info");
      const apiBase = this.getApiBase();
      const dtIso = this.getTargetDateISO();
      const ayanamsa = this.getAyanamsa();

      // 1. Fetch reference data and 2D display payload in parallel
      this.log(`Fetching from ${apiBase}...`, "info");
      const [vedhaRes, kurmaRes] = await Promise.all([
        fetch(`${apiBase}/api/v1/excel/vedha-map-data`),
        fetch(`${apiBase}/api/v1/excel/kurma-display-payload?dt_iso=${encodeURIComponent(dtIso)}&ayanamsa=${ayanamsa}`),
      ]);

      if (!vedhaRes.ok || !kurmaRes.ok) {
        throw new Error(`API Error: Vedha (${vedhaRes.status}), Kurma (${kurmaRes.status})`);
      }

      const vedhaData: VedhaResponse = await vedhaRes.json();
      const kurmaData: KurmaDisplayPayload = await kurmaRes.json();

      this.log(`Retrieved ${vedhaData.count} Vedha entries and 9 Kurma sectors.`, "success");

      // 2. Execute Excel Transaction
      await Excel.run(async (context) => {
        const sheets = context.workbook.worksheets;

        // Ensure sheets exist
        const displaySheet = sheets.getItemOrNullObject("Kurma_Display");
        const tableSheet = sheets.getItemOrNullObject("tblVedhaMap_Sheet");
        await context.sync();

        if (displaySheet.isNullObject || tableSheet.isNullObject) {
          throw new Error("Required worksheets ('Kurma_Display' and 'tblVedhaMap_Sheet') not found in workbook. Please open the official AstroOS template.");
        }

        // ── STEP A: DELETE-then-APPEND on tblVedhaMap ListObject ──────────
        this.log("Managing ListObject lifecycle for 'tblVedhaMap'...", "info");
        const tables = context.workbook.tables;
        const vedhaTable = tables.getItemOrNullObject("tblVedhaMap");
        await context.sync();

        const table2DArray = vedhaData.rows.map(r => [r.pada112, r.position, r.left, r.front, r.right]);

        if (!vedhaTable.isNullObject) {
          // Table exists: clean up old rows to avoid ghost/#N/A records
          const tableRows = vedhaTable.rows;
          tableRows.load("count");
          await context.sync();

          if (tableRows.count > 0) {
            // Delete all existing data rows (keeping header intact)
            tableRows.deleteAllRows();
            await context.sync();
          }

          // Append fresh 2D array in one single batch
          vedhaTable.rows.add(null, table2DArray);
          this.log(`Appended ${table2DArray.length} fresh rows to tblVedhaMap.`, "success");
        } else {
          // Table doesn't exist yet: write headers, data, and create ListObject
          const range = tableSheet.getRange(`A1:E${table2DArray.length + 1}`);
          const fullArray = [["pada112", "position", "left", "front", "right"], ...table2DArray];
          range.values = fullArray;
          tables.add(`tblVedhaMap_Sheet!A1:E${table2DArray.length + 1}`, true /* hasHeaders */);
          this.log(`Created new tblVedhaMap ListObject.`, "success");
        }
        await context.sync();

        // ── STEP B: Batched 2D Array write to Kurma_Display ───────────────
        this.log("Writing 2D sector metrics to Kurma_Display (A6:H14)...", "info");
        const summaryRange = displaySheet.getRange(kurmaData.summary_range);
        summaryRange.values = kurmaData.summary_values;

        // Update header subtitle with evaluated timestamp and overall threat
        const subHeader = displaySheet.getRange("A2");
        subHeader.values = [[
          `Evaluated Timestamp: ${kurmaData.evaluated_at} | Ayanamsa: ${ayanamsa.toUpperCase()} | Summary: ${kurmaData.summary}`
        ]];

        await context.sync();
        this.log("Kurma_Display 2D data assignment complete.", "success");

        // ── STEP C: Post-Write Error-Cell Scan ────────────────────────────
        await this.scanForErrorCells(context, displaySheet);
      });

    } catch (err: any) {
      this.log(`Error during sync: ${err.message || err}`, "error");
      this.setBadge("ERROR", false);
    } finally {
      if (this.syncButton) this.syncButton.disabled = false;
    }
  }

  public async handleAuditOnly(): Promise<void> {
    try {
      this.log("Initiating standalone Error-Cell Audit...", "info");
      await Excel.run(async (context) => {
        const displaySheet = context.workbook.worksheets.getItemOrNullObject("Kurma_Display");
        await context.sync();
        if (displaySheet.isNullObject) {
          throw new Error("Worksheet 'Kurma_Display' not found.");
        }
        await this.scanForErrorCells(context, displaySheet);
      });
    } catch (err: any) {
      this.log(`Audit failed: ${err.message || err}`, "error");
      this.setBadge("ERROR", false);
    }
  }

  /**
   * Scans used ranges for formula errors (#N/A, #REF!, #VALUE!, #NAME?, #DIV/0!)
   */
  private async scanForErrorCells(context: Excel.RequestContext, sheet: Excel.Worksheet): Promise<void> {
    this.log("Scanning Kurma_Display range for formula anomalies...", "info");
    
    // Scan Pada matrix range Y26:AC137
    const padaRange = sheet.getRange("Y26:AC137");
    padaRange.load(["values", "formulas", "address", "rowCount", "columnCount"]);
    await context.sync();

    const values = padaRange.values;
    const errors: { cell: string; value: string; formula: string }[] = [];
    const errorTokens = ["#N/A", "#REF!", "#VALUE!", "#NAME?", "#DIV/0!", "#NUM!", "#NULL!"];

    for (let r = 0; r < values.length; r++) {
      for (let c = 0; c < values[r].length; c++) {
        const valStr = String(values[r][c] || "").trim();
        const formulaStr = String(padaRange.formulas[r][c] || "");

        for (const token of errorTokens) {
          if (valStr.includes(token)) {
            const rowNum = 26 + r;
            const colLetter = ["Y", "Z", "AA", "AB", "AC"][c];
            errors.push({
              cell: `${colLetter}${rowNum}`,
              value: valStr,
              formula: formulaStr,
            });
            break;
          }
        }
      }
    }

    if (errors.length === 0) {
      this.log("✓ Audit PASSED: 0 formula error cells found. All 112 Padas verified.", "success");
      this.setBadge("VERIFIED", true);
    } else {
      this.log(`⚠ Audit WARNING: Found ${errors.length} error cells:`, "warn");
      errors.slice(0, 5).forEach(e => {
        this.log(`  • Cell ${e.cell} => ${e.value} [Formula: ${e.formula}]`, "error");
      });
      if (errors.length > 5) {
        this.log(`  ... and ${errors.length - 5} more error cells.`, "warn");
      }
      this.setBadge(`${errors.length} ERRORS`, false);
    }
  }
}

// Office.js bootstrap
if (typeof Office !== "undefined") {
  Office.onReady((info) => {
    if (info.host === Office.HostType.Excel) {
      const controller = new AstroOSOfficeController();
      controller.init();
    }
  });
}
