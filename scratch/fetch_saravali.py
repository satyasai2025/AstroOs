import urllib.request, ssl, re, json, os

ctx = ssl._create_unverified_context()
base_url = 'https://saravali.github.io/astrology/'
shadbala_url = base_url + 'shadbala.html'

req = urllib.request.Request(shadbala_url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
    html = resp.read().decode('utf-8', errors='ignore')

# Save to a file to inspect
with open('saravali_shadbala.html', 'w', encoding='utf-8') as f:
    f.write(html)

links = re.findall(r'href=[\'"](.*?)[\'"]', html)
print('Links:', links)

# Now let's fetch all links that end with .html
for l in links:
    if l.endswith('.html') and not l.startswith('http') and not l.startswith('../'):
        sub_url = base_url + l
        try:
            r = urllib.request.Request(sub_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(r, context=ctx, timeout=10) as sresp:
                sub_html = sresp.read().decode('utf-8', errors='ignore')
                filename = 'saravali_' + l
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(sub_html)
                print(f'Fetched {sub_url} -> {filename} ({len(sub_html)} bytes)')
        except Exception as e:
            print(f'Failed {sub_url}: {e}')
    elif 'shadbala' in l or 'bala' in l:
        print('Other link:', l)
