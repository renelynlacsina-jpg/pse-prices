import requests, csv, json, os, time
from datetime import datetime
from io import StringIO

TICKERS = [
    'ali.ps', 'cli.ps', 'cnvrg.ps', 'cosco.ps', 'dmc.ps', 'fb.ps',
    'fli.ps', 'glo.ps', 'gma7.ps', 'keepr.ps', 'mer.ps', 'monde.ps',
    'rlc.ps', 'scc.ps',
]

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

results = []
for ticker in TICKERS:
    try:
        url = f'https://stooq.com/q/d/l/?s={ticker}&i=d'
        r = requests.get(url, headers=HEADERS, timeout=10)
        print(f'{ticker}: HTTP {r.status_code}  preview={r.text[:80]}')
        if r.status_code == 200 and ',' in r.text:
            rows = list(csv.DictReader(StringIO(r.text)))
            if rows:
                last = rows[-1]
                price = float(last.get('Close', 0))
                prev  = float(rows[-2]['Close']) if len(rows) >= 2 else price
                pct   = ((price - prev) / prev * 100) if prev else 0
                if price > 0:
                    results.append({
                        'symbol': ticker.upper(),
                        'regularMarketPrice': round(price, 4),
                        'regularMarketChangePercent': round(pct, 4),
                        'exDividendDate': None, 'dividendDate': None,
                        'trailingAnnualDividendRate': None,
                    })
                    print(f'  OK: {price:.4f} ({pct:+.2f}%)')
                    continue
        print(f'  FAILED')
    except Exception as e:
        print(f'  ERROR: {e}')
    time.sleep(0.5)

output = {'updated': datetime.utcnow().isoformat() + 'Z', 'quoteResponse': {'result': results}}
os.makedirs('data', exist_ok=True)
with open('data/prices.json', 'w') as f:
    json.dump(output, f, indent=2)
print(f'\nSaved {len(results)} stocks.')
