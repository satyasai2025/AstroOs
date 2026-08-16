import urllib.request, ssl, re, os
from bs4 import BeautifulSoup

ctx = ssl._create_unverified_context()
base_url = 'https://saravali.github.io/astrology/'

pages = [
    'shadbala.html',
    'shadbala_basics.html',
    'bala_sthana.html',
    'bala_dig.html',
    'bala_kala.html',
    'bala_ayana.html',
    'bala_cheshta.html',
    'bala_naisargika.html',
    'bala_drig.html',
    'bala_summary.html'
]

os.makedirs('scratch/saravali_pages', exist_ok=True)

for p in pages:
    url = base_url + p
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            
            with open(f'scratch/saravali_pages/{p}', 'w', encoding='utf-8') as f:
                f.write(html)
            
            # Convert to clean markdown / text
            soup = BeautifulSoup(html, 'html.parser')
            # remove nav, aside, footer
            for tag in soup(['nav', 'aside', 'footer', 'script', 'style']):
                tag.decompose()
            
            # Get main column
            main = soup.find('div', class_='column is-9') or soup.find('main') or soup.body
            text = main.get_text('\n', strip=True) if main else soup.get_text('\n', strip=True)
            
            with open(f'scratch/saravali_pages/{p}.txt', 'w', encoding='utf-8') as f:
                f.write(text)
            
            print(f'Successfully downloaded and parsed {p} ({len(text)} chars)')
    except Exception as e:
        print(f'Error on {p}: {e}')
