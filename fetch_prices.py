import requests, json, os, re, time
from datetime import datetime
from calendar import timegm

TICKERS = [
    'ALI.PS','CLI.PS','CNVRG.PS','COSCO.PS','DMC.PS','FB.PS',
    'FLI.PS','GLO.PS','GMA7.PS','KEEPR.PS','MER.PS','MONDE.PS','RLC.PS','SCC.PS'
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def to_ts(date_str):
    try:
        return int(timegm(datetime.strptime(date_str.strip(), '%m/%d/%Y').timetuple()))
    except:
        return None

def fetch(ticker):
    sym = ticker.replace('.PS', '')

    # Get company ID
    r = requests.get('https://edge.pse.com.ph/autoComplete/searchCompanyNameSymbol.ax',
                     params={'term': sym}, headers=HEADERS, timeout=15)
    cmpy_id = None
    for res in r.json():
        if res.get('symbol') == sym:
            cmpy_id = res.get('cmpyId')
            break
    if not cmpy_id:
        print(f'  ✗ not found on PSE Edge')
        return None

    # Price
    qr = requests.get('https://edge.pse.com.ph/companyPage/stockData.do',
                      params={'cmpy_id': cmpy_id}, headers=HEADERS, timeout=15)
    price = None
    m = re.search(r'(?:Last Traded|Last Trade|Close)[^<]*</[^>]+>\s*<[^>]+>\s*([\d,]+\.\d{2})',
                  qr.text, re.DOTALL | re.IGNORECASE)
    if m:
        price = float(m.group(1).replace(',', ''))
    else:
        cells = re.findall(r'<td[^>]*>\s*([\d,]+\.\d{2})\s*</td>', qr.text)
        if cells:
            price = float(cells[0].replace(',', ''))
    if not price:
        print(f'  ✗ no price')
        return None

    # Dividends
    dr = requests.get('https://edge.pse.com.ph/companyPage/dividends.do',
                      params={'cmpy_id': cmpy_id}, headers=HEADERS, timeout=15)
    ex_date = pay_date = annual_rate = None
    if dr.status_code == 200:
        print(f'  [div] page fetched, parsing...')
        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', dr.text, re.DOTALL)
        recent = []
        now = datetime.utcnow()
        for row in rows:
            cells = [re.sub(r'<[^>]+>', '', c).strip()
                     for c in re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)]
            if len(cells) < 4:
                continue
            dm = re.match(r'(\d{1,2}/\d{1,2}/\d{4})', cells[0])
            am = re.search(r'([\d.]+)', cells[3])
            if dm and am:
                try:
                    ex_dt = datetime.strptime(dm.group(1), '%m/%d/%Y')
                    age_days = (now - ex_dt).days
                    if 0 <= age_days <= 366:
                        pay_str = cells[2] if len(cells) > 2 else None
                        recent.append((dm.group(1), pay_str, float(am.group(1))))
                except:
                    pass
        if recent:
            annual_rate = round(sum(d[2] for d in recent), 4)
            ex_date = to_ts(recent[0][0])
            pay_date = to_ts(recent[0][1]) if recent[0][1] else None
            print(f'  [div] {len(recent)} payments in last 12mo, annual={annual_rate}')
        else:
            print(f'  [div] no recent dividends found')

    return {
        'symbol': ticker,
        'regularMarketPrice': round(price, 4),
        'regularMarketChangePercent': 0,
        'exDividendDate': ex_date,
        'dividendDate': pay_date,
        'trailingAnnualDividendRate': annual_rate
    }

results = []
for ticker in TICKERS:
    print(f'Fetching {ticker}...')
    data = fetch(ticker)
    if data:
        results.append(data)
        print(f'  ✓ {data["regularMarketPrice"]}')
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
