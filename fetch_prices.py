import requests, json, os, re, time
from datetime import datetime

KEY = os.environ['SCRAPERAPI_KEY']
TICKERS = ['ALI.PS','CLI.PS','CNVRG.PS','COSCO.PS','DMC.PS','FB.PS',
           'FLI.PS','GLO.PS','GMA7.PS','KEEPR.PS','MER.PS','MONDE.PS','RLC.PS','SCC.PS']

def get_price(ticker):
    r = requests.get('https://api.scraperapi.com',
        params={'api_key': KEY, 'url': f'https://finance.yahoo.com/quote/{ticker}/'},
        timeout=60)
    print(f'{ticker}: HTTP {r.status_code}')
    m = re.search(r'"regularMarketPrice":\{"raw":([\d.]+)', r.text)
    if m:
        price = float(m.group(1))
        pm = re.search(r'"regularMarketChangePercent":\{"raw":(-?[\d.]+)', r.text)
        return price, float(pm.group(1)) if pm else 0
    return None, None

results = []
for ticker in TICKERS:
    price, pct = get_price(ticker)
    if price and price > 0:
        results.append({'symbol': ticker, 'regularMarketPrice': round(price,4),
            'regularMarketChangePercent': round(pct,4),
            'exDividendDate': None, 'dividendDate': None, 'trailingAnnualDividendRate': None})
        print(f'  OK: {price}')
    else:
        print(f'  FAILED')
    time.sleep(2)

output = {'updated': datetime.utcnow().isoformat()+'Z', 'quoteResponse': {'result': results}}
os.makedirs('data', exist_ok=True)
with open('data/prices.json','w') as f: json.dump(output, f, indent=2)
print(f'Saved {len(results)} stocks.')
