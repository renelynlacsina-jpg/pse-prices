import yfinance as yf
import json
import os
from datetime import datetime

TICKERS = [
    'ALI.PS', 'CLI.PS', 'CNVRG.PS', 'COSCO.PS', 'DMC.PS', 'FB.PS',
    'FLI.PS', 'GLO.PS', 'GMA7.PS', 'KEEPR.PS', 'MER.PS', 'MONDE.PS',
    'RLC.PS', 'SCC.PS',
]

results = []
for ticker in TICKERS:
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period='5d')
        if hist.empty:
            print(f"ERROR {ticker}: no history data")
            continue
        price = float(hist['Close'].iloc[-1])
        prev = float(hist['Close'].iloc[-2]) if len(hist) >= 2 else price
        pct = ((price - prev) / prev * 100) if prev else 0
        results.append({
            'symbol': ticker,
            'regularMarketPrice': round(price, 4),
            'regularMarketChangePercent': round(pct, 4),
            'exDividendDate': None,
            'dividendDate': None,
            'trailingAnnualDividendRate': None,
        })
        print(f"{ticker}: {price:.4f} ({pct:+.2f}%)")
    except Exception as e:
        print(f"ERROR {ticker}: {e}")

output = {
    'updated': datetime.utcnow().isoformat() + 'Z',
    'quoteResponse': {'result': results},
}

os.makedirs('data', exist_ok=True)
with open('data/prices.json', 'w') as f:
    json.dump(output, f, indent=2)

print(f"\nSaved {len(results)} stocks.")
