import requests, json, os, re, time
from datetime import datetime

TICKERS = [
    'ALI.PS','CLI.PS','CNVRG.PS','COSCO.PS','DMC.PS','FB.PS',
    'FLI.PS','GLO.PS','GMA7.PS','KEEPR.PS','MER.PS','MONDE.PS','RLC.PS','SCC.PS'
]

KEY = os.environ.get('SCRAPERAPI_KEY', '')
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def get_scraperapi(ticker):
    from urllib.parse import quote
    target = f'https://finance.yahoo.com/quote/{ticker}/'
    url = f'https://api.scraperapi.com/?api_key={KEY}&url={quote(target, safe="")}'
    try:
        r = requests.get(url, timeout=60)
        print(f'  [scraperapi] HTTP {r.status_code}')
        if r.status_code != 200:
            print(f'  [scraperapi] body: {r.text[:400]}')
            return None, None
        m = re.search(r'"regularMarketPrice":\{"raw":([\d.]+)', r.text)
        if m:
            price = float(m.group(1))
            pm = re.search(r'"regularMarketChangePercent":\{"raw":(-?[\d.]+)', r.text)
            return price, float(pm.group(1)) if pm else 0
        print(f'  [scraperapi] no price in response; snippet: {r.text[:300]}')
    except Exception as e:
        print(f'  [scraperapi] error: {e}')
    return None, None

def get_phisix(ticker):
    """Free PSE data via phisix-api"""
    sym = ticker.replace('.PS', '')
    try:
        r = requests.get(f'https://phisix-api3.appspot.com/stocks/{sym}.json',
                         headers=HEADERS, timeout=15)
        print(f'  [phisix] HTTP {r.status_code}')
        if r.status_code == 200:
            data = r.json()
            stocks = data.get('stock', [])
            if stocks:
                price = float(stocks[0]['price']['amount'])
                pct = float(stocks[0].get('percent_change', 0))
                return price, pct
    except Exception as e:
        print(f'  [phisix] error: {e}')
    return None, None

def get_pse_edge(ticker):
    """PSE Edge official portal"""
    sym = ticker.replace('.PS', '')
    try:
        r = requests.get('https://edge.pse.com.ph/autoComplete/searchCompanyNameSymbol.ax',
                         params={'term': sym}, headers=HEADERS, timeout=15)
        print(f'  [pse-edge] search HTTP {r.status_code}')
        if r.status_code != 200:
            return None, None
        results = r.json()
        cmpy_id = None
        for res in results:
            if res.get('symbol') == sym:
                cmpy_id = res.get('cmpyId')
                break
        if not cmpy_id:
            print(f'  [pse-edge] symbol not found; got: {results[:2]}')
            return None, None
        print(f'  [pse-edge] cmpyId={cmpy_id}')
        qr = requests.get('https://edge.pse.com.ph/companyPage/stockData.do',
                          params={'cmpy_id': cmpy_id}, headers=HEADERS, timeout=15)
        print(f'  [pse-edge] stockData HTTP {qr.status_code}')
        m = re.search(r'(?:Last Traded|Last Trade|Close)[^<]*</[^>]+>\s*<[^>]+>\s*([\d,]+\.\d{2})',
                      qr.text, re.DOTALL | re.IGNORECASE)
        if m:
            return float(m.group(1).replace(',', '')), 0
        prices = re.findall(r'<td[^>]*>\s*([\d,]+\.\d{2})\s*</td>', qr.text)
        if prices:
            price = float(prices[0].replace(',', ''))
            print(f'  [pse-edge] price from first <td>: {price}')
            return price, 0
        print(f'  [pse-edge] no price found; HTML: {qr.text[:400]}')
    except Exception as e:
        print(f'  [pse-edge] error: {e}')
    return None, None

results = []
for ticker in TICKERS:
    print(f'\nFetching {ticker}...')
    price, pct = None, None

    if KEY:
        price, pct = get_scraperapi(ticker)
        time.sleep(2)

    if price is None:
        price, pct = get_phisix(ticker)
        if price: time.sleep(0.5)

    if price is None:
        price, pct = get_pse_edge(ticker)
        if price: time.sleep(0.5)

    if price and price > 0:
        results.append({
            'symbol': ticker,
            'regularMarketPrice': round(price, 4),
            'regularMarketChangePercent': round(pct or 0, 4),
            'exDividendDate': None,
            'dividendDate': None,
            'trailingAnnualDividendRate': None
        })
        print(f'  ✓ {ticker}: {price}')
    else:
        print(f'  ✗ {ticker}: FAILED all methods')

output = {
    'updated': datetime.utcnow().isoformat() + 'Z',
    'quoteResponse': {'result': results}
}
os.makedirs('data', exist_ok=True)
with open('data/prices.json', 'w') as f:
    json.dump(output, f, indent=2)
print(f'\nSaved {len(results)}/{len(TICKERS)} stocks.')
