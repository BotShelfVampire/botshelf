#!/usr/bin/env python3
"""BSV recipe: pull latest FX rates from the Frankfurter API (ECB reference rates, no key).

Input : base currency (default USD) and comma-separated quote list (default JPY,EUR,GBP).
Output: fx_latest.csv with base, quote, rate, as_of_date, source
Original BSV code, MIT. Cite Frankfurter / ECB if you republish numbers.
"""
import csv, json, sys, urllib.request

def main(base="USD", quotes="JPY,EUR,GBP"):
    base = base.upper().strip()
    qlist = [q.strip().upper() for q in quotes.split(",") if q.strip()]
    url = f"https://api.frankfurter.app/latest?from={base}&to={','.join(qlist)}"
    req = urllib.request.Request(url, headers={"User-Agent": "BSV-fields-recipe/1.0 (practice; +https://botshelfvampire.com)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read().decode("utf-8"))
    as_of = data.get("date", "")
    rates = data.get("rates") or {}
    rows = [{"base": base, "quote": q, "rate": rates[q], "as_of_date": as_of, "source": "frankfurter.app / ECB"}
            for q in qlist if q in rates]
    if not rows:
        raise SystemExit(f"no rates returned for {base} -> {qlist}: {data}")
    with open("fx_latest.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["base", "quote", "rate", "as_of_date", "source"])
        w.writeheader(); w.writerows(rows)
    print(f"wrote {len(rows)} FX rows as_of {as_of} -> fx_latest.csv (source Frankfurter/ECB)")

if __name__ == "__main__":
    main(*sys.argv[1:3])
