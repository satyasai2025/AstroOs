"""
AstroOS — Modern Vector North Indian Diamond Chart SVG Renderer

Generates clean, high-density, resolution-independent SVG markup for North Indian
Kundali diagrams (D1, D9, D10, etc.) styled with the AstroOS design system.
"""

from __future__ import annotations
from typing import Any, Sequence

# Traditional North Indian Diamond House Layout (viewBox 0 0 400 400)
HOUSE_NUMBER_POS = {
    1: (200, 155),
    2: (125, 80),
    3: (75, 125),
    4: (155, 200),
    5: (75, 275),
    6: (125, 320),
    7: (200, 245),
    8: (275, 320),
    9: (325, 275),
    10: (245, 200),
    11: (325, 125),
    12: (275, 80),
}

HOUSE_PLANET_POS = {
    1: (200, 90),
    2: (95, 42),
    3: (42, 95),
    4: (90, 200),
    5: (42, 305),
    6: (95, 358),
    7: (200, 310),
    8: (305, 358),
    9: (358, 305),
    10: (310, 200),
    11: (358, 95),
    12: (305, 42),
}

PLANET_SHORT = {
    "Sun": "Su", "Moon": "Mo", "Mars": "Ma", "Mercury": "Me",
    "Jupiter": "Ju", "Venus": "Ve", "Saturn": "Sa", "Rahu": "Ra",
    "Ketu": "Ke", "Uranus": "Ur", "Neptune": "Ne", "Pluto": "Pl",
    "Ascendant": "As", "Lagna": "As"
}


def render_north_indian_svg(
    ascendant_rashi_num: int,  # 1 to 12 (1 = Aries, 4 = Cancer, etc.)
    planets_in_houses: dict[int, list[str]],  # house_num (1..12) -> list of planet names/abbr
    chart_title: str = "D1 Rasi",
    width: int = 215,
    height: int = 215,
) -> str:

    """
    Renders a modern North Indian Kundali diamond chart as an SVG string.
    """
    svg_lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400" width="{width}" height="{height}" style="font-family: \'Outfit\', \'Inter\', -apple-system, BlinkMacSystemFont, \'Segoe UI\', sans-serif; display: inline-block;">',
        '  <defs>',
        '    <linearGradient id="chartBg" x1="0%" y1="0%" x2="100%" y2="100%">',
        '      <stop offset="0%" stop-color="#ffffff"/>',
        '      <stop offset="100%" stop-color="#f8fafc"/>',
        '    </linearGradient>',
        '    <linearGradient id="kendraGlow" x1="0%" y1="0%" x2="100%" y2="100%">',
        '      <stop offset="0%" stop-color="#fffbeb" stop-opacity="0.9"/>',
        '      <stop offset="100%" stop-color="#fef3c7" stop-opacity="0.4"/>',
        '    </linearGradient>',
        '  </defs>',
        '  <!-- Outer Square with Gold Accent Border -->',
        '  <rect x="6" y="6" width="388" height="388" fill="url(#chartBg)" stroke="#0f172a" stroke-width="2" rx="6"/>',
        '  <!-- Kendra Highlights -->',
        '  <!-- 1st House (Lagna) -->',
        '  <polygon points="200,6 297,103 200,200 103,103" fill="url(#kendraGlow)"/>',
        '  <!-- 4th House -->',
        '  <polygon points="103,103 200,200 103,297 6,200" fill="#f8fafc"/>',
        '  <!-- 7th House -->',
        '  <polygon points="200,200 297,297 200,394 103,297" fill="#f8fafc"/>',
        '  <!-- 10th House -->',
        '  <polygon points="297,103 394,200 297,297 200,200" fill="#f8fafc"/>',
        '  <!-- Main Diagonal Cross Lines -->',
        '  <line x1="6" y1="6" x2="394" y2="394" stroke="#94a3b8" stroke-width="1.2"/>',
        '  <line x1="394" y1="6" x2="6" y2="394" stroke="#94a3b8" stroke-width="1.2"/>',
        '  <!-- Inner Diamond Rhombus -->',
        '  <polygon points="200,6 394,200 200,394 6,200" fill="none" stroke="#0f172a" stroke-width="1.5"/>',
    ]

    # Render Rashi Numbers in Houses
    for house in range(1, 13):
        rashi_num = ((ascendant_rashi_num - 1 + (house - 1)) % 12) + 1
        x, y = HOUSE_NUMBER_POS[house]
        is_kendra = house in (1, 4, 7, 10)
        num_color = "#b45309" if is_kendra else "#64748b"
        font_weight = "800" if is_kendra else "600"
        svg_lines.append(
            f'  <text x="{x}" y="{y}" font-size="11" font-weight="{font_weight}" fill="{num_color}" text-anchor="middle" dominant-baseline="central">{rashi_num}</text>'
        )

    # Render Planets in Houses
    for house, plist in planets_in_houses.items():
        if not plist or house not in HOUSE_PLANET_POS:
            continue
        cx, cy = HOUSE_PLANET_POS[house]
        
        formatted_planets = []
        for p in plist:
            short = PLANET_SHORT.get(p, p[:2])
            formatted_planets.append(short)
            
        chunk_size = 2 if len(formatted_planets) > 2 else 3
        chunks = [
            formatted_planets[i:i + chunk_size]
            for i in range(0, len(formatted_planets), chunk_size)
        ]
        
        line_height = 14
        start_y = cy - ((len(chunks) - 1) * line_height / 2)
        
        for idx, chunk in enumerate(chunks):
            py = start_y + (idx * line_height)
            total_w = len(chunk) * 22
            sx = cx - (total_w / 2) + 11
            for p_idx, p_str in enumerate(chunk):
                px = sx + (p_idx * 22)
                p_color = "#1d4ed8" if p_str == "As" else "#0f172a"
                svg_lines.append(
                    f'  <text x="{px}" y="{py}" font-size="12" font-weight="700" fill="{p_color}" text-anchor="middle" dominant-baseline="central">{p_str}</text>'
                )

    svg_lines.append('</svg>')
    return "\n".join(svg_lines)
