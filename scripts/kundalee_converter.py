#!/usr/bin/env python3
"""KundaleeStore -> AstroOS ResearchCaseBatchImportSchema converter."""
import os, json, re
from datetime import datetime as dt

BATCH_SIZE = 1000
IN = r"C:\Users\rkmau\Downloads\KundaleeStore_Full\KundaleeStore_Full\KundaleeStore\Included\celebrities"
OUT = r"C:\Users\rkmau\Downloads\KundaleeStore_Full\KundaleeStore_Full\KundaleeStore\Imported\cases"

TZMAP = {
    "CST":"America/Chicago","CDT":"America/Chicago",
    "EST":"America/New_York","EDT":"America/New_York",
    "MST":"America/Denver","MDT":"America/Denver",
    "PST":"America/Los_Angeles","PDT":"America/Los_Angeles",
    "GMT":"Etc/GMT","UTC":"Etc/UTC",
    "BST":"Europe/London","MET":"Europe/Paris","MEZ":"Europe/Berlin",
    "EET":"Europe/Helsinki","IST":"Asia/Kolkata","JST":"Asia/Tokyo",
    "AWST":"Australia/Perth","AEST":"Australia/Sydney","AEDT":"Australia/Sydney",
    "EWT":"America/New_York",
}

def iana_tz(raw):
    if not raw: return "UTC"
    h = raw.strip().split()[0]
    b = re.sub(r"h\d+[weEW]$","",h).upper()
    return TZMAP.get(b) or TZMAP.get(h) or "UTC"

CONF = {"AA":"high","A":"high","B":"medium","C":"medium",
        "X":"low","XX":"low","XXX":"low","DD":"low","D":"low"}

ETMAP = {
    "marriage":"Marriage","married":"Marriage","wed":"Marriage",
    "divorce":"Divorce","divorced":"Divorce",
    "death":"Death of Parent","died":"Death of Parent",
    "birth":"Child Birth",
    "accident":"Accident","crash":"Accident","collision":"Accident",
    "surgery":"Surgery","operated":"Surgery",
    "hospital":"Hospitalization","hospitalized":"Hospitalization",
    "travel":"Foreign Travel","relocated":"Foreign Travel",
    "graduate":"Education","graduated":"Education","degree":"Education",
    "award":"Awards","honor":"Awards",
    "promotion":"Promotion","promoted":"Promotion",
    "job change":"Job Change","resigned":"Job Change","fired":"Job Change",
    "injury":"Accident","assault":"Accident",
    "legal":"Litigation","lawsuit":"Litigation","arrested":"Litigation",
    "illness":"Health","cancer":"Health","disease":"Health",
}



def parse(fp):
    with open(fp, encoding="utf-8", errors="replace") as f:
        txt = f.read()
    nm = re.search(r"name:\s*(.+)", txt)
    name = nm.group(1).strip() if nm else ""
    born, tob = None, None
    bm = re.search(r"born_on:\s*(.+)", txt)
    if bm:
        s = bm.group(1).strip()
        dm = re.search(
            r"(\d{1,2}\s+\w+\s+\d{4})\s+(?:at\s+)?(\d{1,2}:\d{2}(?::\d{2})?)", s
        )
        if dm:
            dp, tp = dm.group(1), dm.group(2)
            hh, mm = tp.split(":")[0], tp.split(":")[1]
            tob = f"{hh}:{mm}"
            for fmt in ("%d %B %Y at %H:%M", "%d %B %Y at %H:%M:%S",
                        "%d %B %Y %H:%M"):
                try:
                    born = dt.strptime(f"{dp} at {hh}:{mm}", fmt)
                    break
                except ValueError:
                    pass
    if not born:
        return None
    gm = re.search(r"gender:\s*(\w)", txt)
    g = gm.group(1).upper() if gm else ""
    gender = {"M": "Male", "F": "Female"}.get(g, "Other")
    place, lat, lon = "", None, None
    pm = re.search(r"place:\s*(.+)", txt)
    if pm:
        place = pm.group(1).strip()
        lm = re.search(r"(\d+)\s*([nNsS])\s*(\d+)?", place)
        lom = re.search(r"(\d+)\s*([eEwW])\s*(\d+)?", place)
        dm2 = re.search(r"([+-]?\d+\.\d+)\s+([+-]?\d+\.\d+)", place)
        if lm:
            d, mn = int(lm.group(1)), int(lm.group(3)) if lm.group(3) else 0
            lat = d + mn / 60.0
            lat = -lat if lm.group(2).upper() == "S" else lat
        if lom:
            d, mn = int(lom.group(1)), int(lom.group(3)) if lom.group(3) else 0
            lon = d + mn / 60.0
            lon = -lon if lom.group(2).upper() == "W" else lon
        if dm2 and lat is None:
            lat, lon = float(dm2.group(1)), float(dm2.group(2))
    tm = re.search(r"timezone:\s*(.+)", txt)
    tz = iana_tz(tm.group(1).strip()) if tm else "UTC"
    rm = re.search(r"rodden_rating:\s*(\S+)", txt)
    rodden = rm.group(1).strip().upper() if rm else ""
    btc = CONF.get(rodden, "medium")
    sm = re.search(r"datasource:\s*(.+)", txt)
    source = sm.group(1).strip() if sm else "KundaleeStore"
    evts = []
    ie = False
    for line in txt.split("\n"):
        if line.startswith("START EVENTS"):
            ie = True
            continue
        if ie and line.startswith("END EVENTS"):
            ie = False
            continue
        if ie:
            dm3 = re.search(r"(\d{1,2})\s+(\w+)\s+(\d{4})", line) or \
                  re.search(r"(\d{4})\s+(\w+)\s+(\d{1,2})", line)
            if dm3:
                d, mo, y = dm3.group(1), dm3.group(2), dm3.group(3)
                if len(y) != 4:
                    d, mo, y = y, mo, d
                t = line.strip()
                lo = t.lower()
                et = "Other"
                for kw, val in ETMAP.items():
                    if kw in lo:
                        et = val
                        break
                sev = "Moderate"
                if any(w in lo for w in ["death", "died", "murder", "major", "severe"]):
                    sev = "Major"
                elif any(w in lo for w in ["minor", "slight", "small"]):
                    sev = "Minor"
                evts.append({
                    "type": et,
                    "event_date": f"{d} {mo} {y}",
                    "severity": sev,
                    "verified": True,
                    "confidence": "medium",
                    "source": "KundaleeStore",
                    "description": t[:2000],
                })
    if not evts:
        evts.append({
            "type": "Other",
            "event_date": born.strftime("%Y-%m-%d"),
            "severity": "Minor",
            "verified": False,
            "confidence": "low",
            "source": "KundaleeStore",
            "description": "Birth record",
        })
    return {
        "person": {
            "name": name or "Unknown",
            "gender": gender,
            "dob": born.strftime("%Y-%m-%d"),
            "tob": tob,
            "place": place,
            "latitude": lat,
            "longitude": lon,
            "timezone": tz,
            "source": source,
            "birth_time_confidence": btc,
        },
        "ayanamsa": "lahiri",
        "house_system": "P",
        "divisional_charts": ["D1"],
        "life_events": evts,
        "research_notes": f"Converted: {os.path.basename(fp)}",
        "source_batch": "kundaleestore_v2",
    }



def main():
    os.makedirs(OUT, exist_ok=True)
    files = sorted(f for f in os.listdir(IN) if f.endswith(".txt"))
    print(f"Found {len(files)} .txt files")
    batches = [files[i:i+BATCH_SIZE] for i in range(0, len(files), BATCH_SIZE)]
    print(f"Total batches: {len(batches)}")
    tot, skp = 0, 0
    for bi, batch in enumerate(batches, 1):
        cases, bskp = [], 0
        for fn in batch:
            try:
                c = parse(os.path.join(IN, fn))
                if c: cases.append(c)
                else: bskp += 1
            except Exception: bskp += 1
        if bskp: print(f"  Skipped {bskp} invalid in batch {bi}")
        od = os.path.join(OUT, f"kundalee_batch_{bi:04d}")
        os.makedirs(od, exist_ok=True)
        op = os.path.join(od, f"cases_{bi:04d}.json")
        with open(op, "w", encoding="utf-8") as f:
            json.dump({"cases": cases, "generate_ids": False}, f, indent=2)
        tot += len(cases); skp += bskp
        print(f"  Batch {bi}: saved {op} ({len(cases)} valid)")
    print(f"Done! {tot} valid, {skp} invalid (skipped).")

if __name__ == "__main__": main()
