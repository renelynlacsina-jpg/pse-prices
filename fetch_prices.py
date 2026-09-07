import requests
import json
import os
import time
from datetime import datetime

TICKERS = [
    'ALI.PS', 'CLI.PS', 'CNVRG.PS', 'COSCO.PS', 'DMC.PS', 'FB.PS',
    'FLI.PS', 'GLO.PS', 'GMA7.PS', 'KEEPR.PS', 'MER.PS', 'MONDE.PS',
    'RLC.PS', 'SCC.PS'
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'application/json',
    'Referer': 'https://finance.yahoo.com',
}

def get_price(ticker):
    url = f'https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=5d'
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        data = r.json()
        meta = data['chart']['result'][0]['meta']
        price = meta.get('regularMarketPrice') or meta.get('chartPreviousClose', 0)
        prev = meta.get('previousClose') or meta.get('chartPreviousClose', price)
        pct = ((price - prev) / prev * 100) if prev else 0
        return float(price), float(pct)
    except Exception as e:
        print(f"  {ticker} error: {e}")
        return None, None

results = []
for ticker in TICKERS:
    price, pct = get_price(ticker)
    if price and price > 0:
        results.append({
            'symbol': ticker,
            'regularMarketPrice': round(price, 4),
            'regularMarketChangePercent': round(pct, 4),
            'exDividendDate': None,
            'dividendDate': None,
            'trailingAnnualDividendRate': None,
        })
        print(f"{ticker}: {price:.4f} ({pct:+.2f}%)")
    else:
        print(f"ERROR {ticker}: no price data")
    time.sleep(0.3)

output = {
    'updated': datetime.utcnow().isoformat() + 'Z',
    'quoteResponse': {'result': results},
}

os.makedirs('data', exist_ok=True)
with open('data/prices.json', 'w') as f:
    json.dump(output, f, indent=2)

print(f"\nSaved {len(results)} stocks.")
