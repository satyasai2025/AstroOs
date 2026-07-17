"""Generate RF-PADA CSV — 108 padas from approved mathematical derivation."""
rashi_list = ["aries","taurus","gemini","cancer","leo","virgo","libra","scorpio","sagittarius","capricorn","aquarius","pisces"]
deg_per_pada = 360.0 / 108.0  # 3.333333...
nak_list = ["ashwini","bharani","krittika","rohini","mrigashira","ardra","punarvasu","pushya","ashlesha","magha","purva_phalguni","uttara_phalguni","hasta","chitra","swati","vishakha","anuradha","jyeshtha","mula","purva_ashadha","uttara_ashadha","shravana","dhanishtha","shatabhisha","purva_bhadrapada","uttara_bhadrapada","revati"]

lines = ["_record_id,_dataset_id,_record_type,_version,_is_deleted,pada_id,nakshatra_name,nakshatra_id,pada_number,navamsha_rashi,start_degree,end_degree"]
for i in range(108):
    nak_idx = i // 4
    pada_num = (i % 4) + 1
    nav_rashi = rashi_list[i % 12]
    start = round(i * deg_per_pada, 6)
    end = round((i + 1) * deg_per_pada, 6)
    rid = f"ASTRO-REC-PADA-{i+1:06d}"
    did = "ASTRO-RF-PADA-v1.0.0"
    lines.append(f"{rid},{did},reference,1,false,{i+1},{nak_list[nak_idx]},{nak_idx+1},{pada_num},{nav_rashi},{start},{end}")

with open("/c/Users/rkmau/.claude/projects/c--Users-rkmau--claude/datasets/rf/padas/ASTRO-RF-PADA-v1.0.0/ASTRO-RF-PADA-v1.0.0_CSV.csv", "w") as f:
    f.write("\n".join(lines) + "\n")
print("RF-PADA CSV generated")
