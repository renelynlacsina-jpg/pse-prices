import requests
from bs4 import BeautifulSoup
import json, os, re, time
from datetime import datetime

TICKERS = {
    'ALI.PS': 'ALI:PSE',
    'CLI.PS': 'CLI:PSE',
    'CNVRG.PS': 'CNVRG:PSE',
    'COSCO.PS': 'COSCO:PSE',
    'DMC.PS': 'DMC:PSE',
    'FB.PS': 'FB:PSE',
    'FLI.PS': 'FLI:PSE',
    'GLO.PS': 'GLO:PSE',
    'GMA7.PS': 'GMA7:PSE',
    'KEEPR.PS': 'KEEPR:PSE',
    'MER.PS': 'MER:PSE',
    'MONDE.PS': 'MONDE:PSE',
    'RLC.PS': 'RLC:PSE',
    'SCC.PS': 'SCC:PSE',
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

def scrape(gf_sym):
    r = requests.get(f'https://www.google.com/finance/quote/{gf_sym}', headers=HEADERS, timeout=15)
    print(f'  HTTP {r.status_code}  len={len(r.text)}')
    if r.status_code != 200:
        return None, None
    html = r.text

    # Try data attribute
    m = re.search(r'data-last-price="([\d.]+)"', html)
    if m:
        price = float(m.group(1))
        mp = re.search(r'data-prev-close="([\d.]+)"', html)
        prev = float(mp.group(1)) if mp else price
        return price, ((price - prev) / prev * 100) if prev else 0

    # Try embedded JSON
    m = re.search(r'"regularMarketPrice"[:\s]+([\d.]+)', html)
    if m:
        return float(m.group(1)), 0

    # Try BeautifulSoup class scan
    soup = BeautifulSoup(html, 'html.parser')
    for cls in [['YMlKec', 'fxKbKc'], ['kf1m4'], ['IsqQVc']]:
        el = soup.find(class_=cls)
        if el:
            txt = re.sub(r'[^\d.]', '', el.get_text())
            try:
                p = float(txt)
                if p > 0:
                    return p, 0
            except: pass

    # Print snippet for debugging
    print(f'  snippet: {html[1800:2200]}')
    return None, None

results = []
for ps_sym, gf_sym in TICKERS.items():
    print(f'\n{ps_sym}:')
    price, pct = scrape(gf_sym)
    if price and price > 0:
        results.append({
            'symbol': ps_sym,
            'regularMarketPrice': round(price, 4),
            'regularMarketChangePercent': round(float(pct or 0), 4),
            'exDividendDate': None,
            'dividendDate': None,
            'trailingAnnualDividendRate': None,
        })
        print(f'  OK: {price:.4f} ({pct:+.2f}%)')
    else:
        print(f'  FAILED')
    time.sleep(1.5)

output = {'updated': datetime.utcnow().isoformat() + 'Z', 'quoteResponse': {'result': results}}
os.makedirs('data', exist_ok=True)
with open('data/prices.json', 'w') as f:
    json.dump(output, f, indent=2)
print(f'\nSaved {len(results)} stocks.')
