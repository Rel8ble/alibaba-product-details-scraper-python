"""Compare Alibaba suppliers at YOUR order quantity.

Runs the Alibaba Product Details Scraper on Apify for a keyword (and/or a list of
product URLs), then works out for every product the unit price and lead time at the
quantity you plan to order, and writes alibaba_shortlist.csv sorted by price.

    pip install -r requirements.txt
    APIFY_TOKEN=<YOUR_APIFY_TOKEN> python example.py
"""
import csv
import os

from apify_client import ApifyClient

QTY = 500                       # units you plan to order
SEARCH_TERMS = ["yoga mat"]     # keywords; each product found is opened in full
PRODUCT_URLS = []               # or paste product URLs / bare product IDs here
MAX_PER_SEARCH = 30


def price_at(p, qty):
    for t in p.get("priceTiers") or []:
        if t["minQuantity"] <= qty and (t["maxQuantity"] is None or qty <= t["maxQuantity"]):
            return t["price"]
    return p.get("priceMin")


def lead_at(p, qty):
    for band in p.get("leadTimes") or []:
        if band["minQuantity"] <= qty <= (band["maxQuantity"] or 10**9):
            return band["days"]
    return None  # above the largest band: "to be negotiated"


def main():
    client = ApifyClient(os.environ.get("APIFY_TOKEN", "<YOUR_APIFY_TOKEN>"))
    run_input = {"maxProductsPerSearch": MAX_PER_SEARCH, "includeAds": False}
    if SEARCH_TERMS:
        run_input["searchTerms"] = SEARCH_TERMS
    if PRODUCT_URLS:
        run_input["productUrls"] = PRODUCT_URLS
    run = client.actor("rel8ble/alibaba-product-details-scraper").call(run_input=run_input)

    rows, seen = [], set()
    for p in client.dataset(run["defaultDatasetId"]).iterate_items():
        if p["productId"] in seen:
            continue
        seen.add(p["productId"])
        if p.get("moq") and p["moq"] > QTY:
            continue  # cannot buy this few
        price = price_at(p, QTY)
        rows.append({
            "unit_price_usd": price,
            "order_total_usd": round(price * QTY, 2) if price else None,
            "lead_days": lead_at(p, QTY),
            "moq": p.get("moq"),
            "sample_price": p.get("samplePrice"),
            "supplier": p.get("supplierName"),
            "years_on_alibaba": p.get("supplierYearsOnAlibaba"),
            "verified": p.get("verifiedSupplier"),
            "on_time": p.get("onTimeDeliveryRate"),
            "rating": p.get("supplierRating"),
            "certificates": "/".join(sorted({c["name"] for c in p.get("certificates") or []})),
            "title": (p.get("title") or "")[:80],
            "url": p.get("url"),
        })

    rows.sort(key=lambda r: r["unit_price_usd"] if r["unit_price_usd"] is not None else 1e9)
    if not rows:
        print("No products with MOQ <=", QTY)
        return
    with open("alibaba_shortlist.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    print(f"{len(rows)} products you can order at {QTY} units -> alibaba_shortlist.csv\n")
    for r in rows[:15]:
        print(f"${r['unit_price_usd']:>6} | {r['lead_days'] or '?':>3} days | MOQ {r['moq']:>4} | "
              f"{r['years_on_alibaba']:>2} yrs | {'verified' if r['verified'] else 'unverified':10} | "
              f"{r['on_time'] or '-':>6} on time | {r['supplier']}")

    verified = [r for r in rows if r["verified"] and (r["years_on_alibaba"] or 0) >= 5]
    if verified:
        best = verified[0]
        print(f"\nCheapest verified supplier with 5+ years: ${best['unit_price_usd']} "
              f"(${best['order_total_usd']} for {QTY}) - {best['supplier']}")


if __name__ == "__main__":
    main()
