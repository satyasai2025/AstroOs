# Compare Charts - End-to-End Test Instructions

## Test Environment
- **URL**: `http://localhost:3000/charts/compare`
- **Browser**: Chrome/Firefox/Edge (latest)
- **Viewport**: Desktop (1920x1080), Tablet (768x1024), Mobile (375x667)

---

## Test Suite: Compare Charts Workflow

### TC-01: Empty State Load
**Steps:**
1. Navigate to `http://localhost:3000/charts/compare`
2. Observe initial state

**Expected:**
- Page title: "Compare Birth Charts"
- Empty state message: "Compare two or more charts to discover similarities and differences"
- Button: "[+ Select Charts]" visible and clickable
- No charts displayed in workspace

---

### TC-02: Chart Selection Modal - Open
**Steps:**
1. From empty state, click "[+ Select Charts]"
2. Observe modal

**Expected:**
- Modal opens with title "Choose Charts"
- List of available charts with checkboxes:
  - Rajesh Birth Chart (checked by default)
  - Meena Birth Chart
  - Kunal Career Chart
  - Test Subject
- Counter: "0 of 4 charts selected" (or "1 of 4" if one pre-checked)
- "Cancel" button and "Compare →" button (disabled initially)

---

### TC-03: Chart Selection - Validation Rules
**Steps:**
1. Open modal
2. Try clicking "Compare →" with 0 charts selected
3. Check 1 chart, try "Compare →"
4. Check 2nd chart, try "Compare →"
5. Check 5th chart (should be prevented)
6. Uncheck, re-check different combination

**Expected:**
- "Compare →" disabled when < 2 charts selected
- "Compare →" enabled when ≥ 2 charts selected
- Maximum 4 charts enforced (5th checkbox disabled)
- Selection counter updates in real-time: "X of 4 charts selected"
- Error message when < 2: "(minimum 2 required)"

---

### TC-04: Chart Selection - Cancel Flow
**Steps:**
1. Open modal
2. Select 2 charts
3. Click "Cancel"
4. Verify state reset

**Expected:**
- Modal closes
- No charts carried over to workspace
- Return to empty state

---

### TC-05: Comparison Workspace Load
**Steps:**
1. Select exactly 2 charts (Rajesh, Meena)
2. Click "Compare →"
3. Observe workspace

**Expected:**
- Workspace loads with side-by-side layout
- Header shows "Comparison Workspace" with similarity score badge
- Left panel: Chart A (Rajesh) with North Chart
- Right panel: Chart B (Meena) with North Chart
- Overview section: Lagna, Moon, Dasha, Yogas, Strength for both
- Tabs: Planets | Houses | Dasha | Yogas | AI Summary | Saved
- Footer: Export buttons (PDF, CSV) + Save Comparison

---

### TC-06: Planet Comparison Tab
**Steps:**
1. In workspace, click "Planets" tab (default active)
2. Review planet comparison table

**Expected:**
- Table columns: Planet | Chart A | Chart B | Difference
- Each row shows:
  - Planet name (Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu)
  - Value for Chart A (sign + house)
  - Value for Chart B (sign + house)
  - Difference badge with color:
    - 🟢 Green "Same" when identical
    - 🟡 Yellow "Similar" when minor diff (same element)
    - 🔴 Red "Different" when major diff
- No text overlap in table cells
- Horizontal scroll on mobile if needed

---

### TC-07: Houses Tab
**Steps:**
1. Click "Houses" tab
2. Review house comparison

**Expected:**
- Two-column grid: Chart A houses | Chart B houses
- Each house shows: House number, Lord planet, Sign, Strength
- No text overlap
- Responsive grid on tablet/mobile

---

### TC-08: Dasha Tab
**Steps:**
1. Click "Dasha" tab
2. Review dasha comparison

**Expected:**
- Side-by-side dasha cards for Chart A and Chart B
- Shows current Mahadasha for each
- Analysis text based on similarity score:
  - ≥80%: "Both charts are currently under similar dasha influence"
  - 50-79%: "Charts are under moderately different dasha periods"
  - <50%: "Significant dasha difference — very different current life phases"

---

### TC-09: Yogas Tab
**Steps:**
1. Click "Yogas" tab
2. Review yoga comparison

**Expected:**
- Two panels showing yoga counts and lists
- Each yoga as badge/tag
- Truncation if >5 yogas ("+X more")
- No text overlap

---

### TC-10: AI Summary Tab
**Steps:**
1. Click "AI Summary" tab
2. Review summary

**Expected:**
- Similarity score prominently displayed (large number + %)
- Major differences listed with red dot indicators
- Recommendations section with context-aware text
- Green background for recommendations box

---

### TC-11: Saved Comparisons Panel
**Steps:**
1. Scroll to bottom or click "Saved" tab
2. Observe saved comparisons list

**Expected:**
- Shows all previously saved comparisons from localStorage
- Each entry: name, chart count, modified date, pin status
- Click to reopen (logs to console for now)
- Delete button for unpinned entries
- Empty state message when none saved

---

### TC-12: Export PDF
**Steps:**
1. In workspace, click "📄 Export PDF"
2. Observe browser behavior

**Expected:**
- PDF generation triggered (alert or download)
- File name pattern: `comparison-{chartA}-{chartB}-{date}.pdf`
- Content includes:
  - Header: "AstroOS Comparison Report"
  - Overview tables for both charts
  - Planet comparison table with color-coded differences
  - AI Summary with similarity score and differences
  - Footer with generation timestamp

---

### TC-13: Export CSV
**Steps:**
1. In workspace, click "📊 Export CSV"
2. Observe browser behavior

**Expected:**
- CSV download triggered
- File name pattern: `comparison-{chartA}-{chartB}-{date}.csv`
- Content sections:
  - === Planet Comparison === (Planet,Chart A,Chart B,Difference)
  - === Yogas Comparison === (Chart A Yogas,Chart B Yogas)
  - === Dasha Comparison === (Chart A Dasha,Chart B Dasha)
- UTF-8 encoding

---

### TC-14: Save Comparison
**Steps:**
1. In workspace, click "💾 Save Comparison"
2. Enter name in prompt (if modal) or verify auto-save

**Expected:**
- Comparison saved to localStorage
- Appears in Saved Comparisons panel immediately
- Includes: name, chart IDs, comparison type, timestamp, pinned=false

---

### TC-15: Persistence - Page Reload
**Steps:**
1. Save a comparison
2. Reload page (F5)
3. Navigate to `/charts/compare`

**Expected:**
- Saved Comparisons panel shows previously saved entry
- Clicking it loads the comparison data
- All tabs and data restore correctly

---

### TC-16: Text Overlap Verification
**Steps:**
1. Test on multiple viewports: Desktop, Tablet, Mobile
2. Check all tabs for text overlap
3. Check modal for label truncation

**Expected:**
- No overlapping text in any component
- Table cells use `overflow-x-auto` on mobile
- Modal labels truncate with ellipsis
- Chart labels in NorthIndianChart don't overlap (verified in earlier analysis)
- Force graph labels have collision avoidance (verified in earlier analysis)

---

### TC-17: Navigation Integration
**Steps:**
1. Open main app navigation (NavPanel)
2. Find "Compare Charts" link
3. Click it

**Expected:**
- "Compare Charts" visible in NavPanel (Charts & Analysis section)
- Not disabled (`disabled: false`)
- Click navigates to `/charts/compare`
- Loads empty state correctly

---

### TC-18: Keyboard Accessibility
**Steps:**
1. Navigate entire flow using only keyboard (Tab, Enter, Escape, Arrow keys)
2. Test modal focus trap

**Expected:**
- All interactive elements reachable via Tab
- Modal traps focus (Tab cycles within modal)
- Escape closes modal
- Enter/Space activates buttons
- Focus indicators visible

---

### TC-19: Error Handling
**Steps:**
1. Clear localStorage, test saved comparisons panel
2. Test with invalid chart data
3. Test export with no selection

**Expected:**
- Empty state handled gracefully
- No console errors
- User-friendly messages for edge cases

---

### TC-20: Performance
**Steps:**
1. Open workspace with 4 charts selected
2. Switch between all tabs rapidly
3. Check for lag

**Expected:**
- Tab switches < 100ms
- No visual flickering
- Smooth animations (if any)
- Memory stable (no leaks on repeated open/close)

---

## Test Results Template

| Test Case | Status | Browser | Viewport | Notes |
|-----------|--------|---------|----------|-------|
| TC-01 | Pass/Fail | | | |
| TC-02 | Pass/Fail | | | |
| TC-03 | Pass/Fail | | | |
| TC-04 | Pass/Fail | | | |
| TC-05 | Pass/Fail | | | |
| TC-06 | Pass/Fail | | | |
| TC-07 | Pass/Fail | | | |
| TC-08 | Pass/Fail | | | |
| TC-09 | Pass/Fail | | | |
| TC-10 | Pass/Fail | | | |
| TC-11 | Pass/Fail | | | |
| TC-12 | Pass/Fail | | | |
| TC-13 | Pass/Fail | | | |
| TC-14 | Pass/Fail | | | |
| TC-15 | Pass/Fail | | | |
| TC-16 | Pass/Fail | | | |
| TC-17 | Pass/Fail | | | |
| TC-18 | Pass/Fail | | | |
| TC-19 | Pass/Fail | | | |
| TC-20 | Pass/Fail | | | |

---

## Sign-off
- **Tested by**: _______________
- **Date**: _______________
- **Overall**: PASS / FAIL
- **Blocking issues**: _______________