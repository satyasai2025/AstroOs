"""
AstroOS — Wikidot Vedic Astrology Canonical Knowledge Harvester
==============================================================

Crawls, cleans, structures, and persists all 150+ articles from
http://vedicastrology.wikidot.com/ into a structured, indexed
Shastric knowledge repository.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, List, Optional, Tuple

BASE_URL = "http://vedicastrology.wikidot.com"
OUTPUT_DIR = Path("docs/wikidot_canonical_knowledge")


def clean_html_to_markdown(html_content: str, title: str, url: str) -> str:
    """Extracts text, headers, lists, code, and tables from Wikidot HTML."""
    # Find page-content div
    match = re.search(r'<div id="page-content"[^>]*>(.*?)</div>\s*<div id="page-info', html_content, re.DOTALL | re.IGNORECASE)
    body = match.group(1) if match else html_content

    # Clean script, style, comments
    body = re.sub(r'<script[^>]*>.*?</script>', '', body, flags=re.DOTALL | re.IGNORECASE)
    body = re.sub(r'<style[^>]*>.*?</style>', '', body, flags=re.DOTALL | re.IGNORECASE)
    body = re.sub(r'<!--.*?-->', '', body, flags=re.DOTALL)

    # Convert headers
    body = re.sub(r'<h1[^>]*>(.*?)</h1>', r'\n# \1\n', body, flags=re.DOTALL | re.IGNORECASE)
    body = re.sub(r'<h2[^>]*>(.*?)</h2>', r'\n## \1\n', body, flags=re.DOTALL | re.IGNORECASE)
    body = re.sub(r'<h3[^>]*>(.*?)</h3>', r'\n### \1\n', body, flags=re.DOTALL | re.IGNORECASE)
    body = re.sub(r'<h4[^>]*>(.*?)</h4>', r'\n#### \1\n', body, flags=re.DOTALL | re.IGNORECASE)

    # Convert paragraphs and linebreaks
    body = re.sub(r'<p[^>]*>(.*?)</p>', r'\n\1\n', body, flags=re.DOTALL | re.IGNORECASE)
    body = re.sub(r'<br\s*/?>', r'\n', body, flags=re.IGNORECASE)

    # Convert list items
    body = re.sub(r'<li[^>]*>(.*?)</li>', r'\n- \1', body, flags=re.DOTALL | re.IGNORECASE)

    # Convert tables roughly to markdown rows
    body = re.sub(r'<tr[^>]*>', r'\n', body, flags=re.IGNORECASE)
    body = re.sub(r'<td[^>]*>(.*?)</td>', r'| \1 ', body, flags=re.DOTALL | re.IGNORECASE)
    body = re.sub(r'<th[^>]*>(.*?)</th>', r'| **\1** ', body, flags=re.DOTALL | re.IGNORECASE)

    # Strip remaining HTML tags
    clean_text = re.sub(r'<[^>]+>', '', body)
    
    # Unescape HTML entities
    clean_text = clean_text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"').replace('&#39;', "'")

    # Normalize excessive newlines
    clean_text = re.sub(r'\n{3,}', '\n\n', clean_text).strip()

    md = f"# {title}\n\n**Source URL:** [{url}]({url})\n\n---\n\n{clean_text}\n"
    return md


def categorize_article(slug: str) -> str:
    """Categorizes the article into standard architectural domains."""
    slug = slug.lower()

    if any(k in slug for k in ["moe", "machine-learning", "auto-m-l", "lstm", "neural", "espcn", "gpu", "ai-tutorial", "decision-maker", "cartopy", "programming"]):
        return "04_ai_and_computational_systems"
    elif any(k in slug for k in ["narendra-modi", "indira-gandhi", "donald-trump", "kejriwal", "amitabh", "amir-khan", "prophet", "david-cameron", "yogi", "gopinath", "swami-ramakrishna", "lord-ram"]):
        return "05_natal_case_studies"
    elif any(k in slug for k in ["sensex", "gold", "silver", "iron", "rain", "weather", "earthquake", "cyclone", "war", "fani", "biporjoy", "medini", "uttarakhand", "plassey", "alexander", "national-income"]):
        return "06_medini_and_financial"
    elif any(k in slug for k in ["sarvato-bhadra", "sapta-nadi", "sudarshana", "kalachakra", "divisional", "return"]):
        return "03_chakras_and_special_systems"
    elif any(k in slug for k in ["ashtaka", "bhrigu-bindu", "arudha", "dashaa", "vimshottari", "laghu-parashari", "main-strength", "shadbala", "yoga", "friendship", "planetary-war", "sadharmi"]):
        return "02_classical_predictive_principles"
    else:
        return "01_astronomical_foundations"


def harvest_all_wikidot_articles():
    print("=" * 80)
    print("          ASTROOS: WIKIDOT CANONICAL KNOWLEDGE HARVESTER                       ")
    print("=" * 80)

    # 1. Read sitemap or get full page list
    sitemap_cache = Path(r"C:\Users\rkmau\.gemini\antigravity\brain\2cd32124-529e-413b-a3a5-af469d006df5\.system_generated\steps\1351\content.md")
    if not sitemap_cache.exists():
        print(f"Fetching sitemap from {BASE_URL}/system:list-all-pages...")
        req = urllib.request.Request(f"{BASE_URL}/system:list-all-pages", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
    else:
        html = sitemap_cache.read_text(encoding="utf-8", errors="ignore")

    matches = re.findall(r'href=[\"\'](/[^\"\'#:]+)[\"\']', html)
    raw_slugs = sorted(list(set(m for m in matches if not m.startswith("/_") and not m.startswith("/admin") and not m.startswith("/common--"))))

    print(f"Total Unique Vedic Astrology Pages to Harvest: {len(raw_slugs)}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for cat in [
        "01_astronomical_foundations",
        "02_classical_predictive_principles",
        "03_chakras_and_special_systems",
        "04_ai_and_computational_systems",
        "05_natal_case_studies",
        "06_medini_and_financial",
    ]:
        (OUTPUT_DIR / cat).mkdir(parents=True, exist_ok=True)

    manifest = []
    success_count = 0

    for idx, slug in enumerate(raw_slugs, start=1):
        clean_slug = slug.strip("/")
        if not clean_slug:
            continue

        url = f"{BASE_URL}/{clean_slug}"
        category = categorize_article(clean_slug)
        title = clean_slug.replace("-", " ").title()
        file_path = OUTPUT_DIR / category / f"{clean_slug}.md"

        print(f"[{idx}/{len(raw_slugs)}] Harvesting: {title} -> {category}/...")

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            with urllib.request.urlopen(req, timeout=15) as response:
                page_html = response.read().decode("utf-8", errors="ignore")

            md_content = clean_html_to_markdown(page_html, title, url)
            file_path.write_text(md_content, encoding="utf-8")
            manifest.append({
                "slug": clean_slug,
                "title": title,
                "category": category,
                "url": url,
                "file": str(file_path.as_posix()),
                "status": "SAVED",
            })
            success_count += 1
            time.sleep(0.2)  # Gentle crawl delay
        except Exception as e:
            print(f"  [ERROR] Failed to fetch {url}: {e}")
            manifest.append({
                "slug": clean_slug,
                "title": title,
                "category": category,
                "url": url,
                "error": str(e),
                "status": "FAILED",
            })

    # Write Master Index
    index_md = "# WIKIDOT VEDIC ASTROLOGY CANONICAL KNOWLEDGE REPOSITORY\n\n"
    index_md += f"**Total Articles Harvested:** `{success_count} / {len(raw_slugs)}`\n"
    index_md += f"**Harvest Date:** `{time.strftime('%Y-%m-%d %H:%M:%S')}`\n\n---\n\n"

    for cat in sorted(list(set(m["category"] for m in manifest))):
        index_md += f"## {cat.replace('_', ' ').title()}\n\n"
        cat_items = [m for m in manifest if m.get("category") == cat and m.get("status") == "SAVED"]
        for item in cat_items:
            rel_path = item["file"].replace("docs/wikidot_canonical_knowledge/", "")
            index_md += f"- [{item['title']}](./{rel_path}) ([Source]({item['url']}))\n"
        index_md += "\n"

    (OUTPUT_DIR / "README.md").write_text(index_md, encoding="utf-8")
    (OUTPUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print("=" * 80)
    print(f"[OK] Harvest Complete! {success_count} articles saved to {OUTPUT_DIR.resolve()}")
    print("=" * 80)


if __name__ == "__main__":
    harvest_all_wikidot_articles()
