import requests, json, os, re, time
from datetime import datetime

TICKERS = [
    'ALI.PS','CLI.PS','CNVRG.PS','COSCO.PS','DMC.PS','FB.PS',
    'FLI.PS','GLO.PS','GMA7.PS','KEEPR.PS','MER.PS','MONDE.PS','RLC.PS','SCC.PS'
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def get_price(ticker):
    sym = ticker.replace('.PS', '')
    try:
        r = requests.get('https://edge.pse.com.ph/autoComplete/searchCompanyNameSymbol.ax',
                         params={'term': sym}, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            print(f'  search HTTP {r.status_code}')
            return None, None
        cmpy_id = None
        for res in r.json():
            if res.get('symbol') == sym:
                cmpy_id = res.get('cmpyId')
                break
        if not cmpy_id:
            print(f'  symbol not found in PSE Edge')
            return None, None
        qr = requests.get('https://edge.pse.com.ph/companyPage/stockData.do',
                          params={'cmpy_id': cmpy_id}, headers=HEADERS, timeout=15)
        m = re.search(r'(?:Last Traded|Last Trade|Close)[^<]*</[^>]+>\s*<[^>]+>\s*([\d,]+\.\d{2})',
                      qr.text, re.DOTALL | re.IGNORECASE)
        if m:
            return float(m.group(1).replace(',', '')), 0
        prices = re.findall(r'<td[^>]*>\s*([\d,]+\.\d{2})\s*</td>', qr.text)
        if prices:
            return float(prices[0].replace(',', '')), 0
        print(f'  no price found in stockData page')
    except Exception as e:
        print(f'  error: {e}')
    return None, None

results = []
for ticker in TICKERS:
    print(f'Fetching {ticker}...')
    price, pct = get_price(ticker)
    if price and price > 0:
        results.append({
            'symbol': ticker,
            'regularMarketPrice': round(price, 4),
            'regularMarketChangePercent': round(pct or 0, 4),
            'exDividendDate': None,
            'dividendDate': None,
            'trailingAnnualDividendRate': None
        })
        print(f'  ✓ {price}')
    else:
        print(f'  ✗ FAILED')
    time.sleep(0.5)

output = {
    'updated': datetime.utcnow().isoformat() + 'Z',
    'quoteResponse': {'result': results}
}
os.makedirs('data', exist_ok=True)
with open('data/prices.json', 'w') as f:
    json.dump(output, f, indent=2)
print(f'\nSaved {len(results)}/{len(TICKERS)} stocks.')
