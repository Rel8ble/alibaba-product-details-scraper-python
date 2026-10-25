# Alibaba Product Details Scraper (Python): price tiers, MOQ, SKUs, specs and supplier data as JSON

Get full Alibaba product pages as JSON from Python: the quantity price ladder, MOQ, every SKU, specifications, certificates, lead times, sample price, package size and the verified-supplier card behind each product. Give it product URLs, bare product IDs or a keyword. No browser, no Alibaba account, no API key from Alibaba.

> I built this actor; it's a paid tool on Apify ($2.50 per 1,000 products, with Apify's free trial credit). Store page: https://apify.com/rel8ble/alibaba-product-details-scraper

## Quick start (Python)

```bash
pip install apify-client
```

```python
from apify_client import ApifyClient

client = ApifyClient("<YOUR_APIFY_TOKEN>")

run = client.actor("rel8ble/alibaba-product-details-scraper").call(run_input={
    "productUrls": [
        "https://www.alibaba.com/product-detail/ALOVA-Latest-Model-Bluetooth-6-0_1601511059774.html",
        "1601617846699",
    ],
    "searchTerms": ["yoga mat"],
    "maxProductsPerSearch": 30,
    "includeAds": False,
})

for p in client.dataset(run["defaultDatasetId"]).iterate_items():
    tiers = ", ".join(f"{t['minQuantity']}+: ${t['price']}" for t in p["priceTiers"])
    print(p["title"][:50], "| MOQ", p["moq"], "|", tiers or p["priceText"], "|", p["supplierName"])
```

Get your token at https://console.apify.com/settings/integrations.

## Node.js

```javascript
import { ApifyClient } from 'apify-client';

const client = new ApifyClient({ token: '<YOUR_APIFY_TOKEN>' });
const run = await client.actor('rel8ble/alibaba-product-details-scraper').call({
    searchTerms: ['bluetooth speaker'],
    maxProductsPerSearch: 20,
    includeAds: false,
});
const { items } = await client.dataset(run.defaultDatasetId).listItems();
for (const p of items) console.log(p.priceMin, p.moq, p.leadTimes[0]?.days, p.supplierYearsOnAlibaba, p.url);
```

## Input

| Field | Default | Description |
|---|---|---|
| `productUrls` | - | Product URLs (`https://www.alibaba.com/product-detail/..._1601511059774.html`) or bare product IDs |
| `searchTerms` | - | Keywords or alibaba.com search URLs; each product found is opened in full |
| `maxProductsPerSearch` | 20 | Product pages opened per search term. 0 = everything (up to about 960) |
| `includeAds` | true | Also open sponsored products from searches (flagged `isAd`) |

## What a row looks like

From a real run on 24 Oct 2026, trimmed (each row has about 75 fields):

```json
{
    "productId": "1601511059774",
    "title": "ALOVA Latest Model Bluetooth 6.0 Earphone IPX7 Bone Conduction Headset Waterproof Headphone Wireless Earbuds with Mic",
    "priceTiers": [
        { "minQuantity": 10, "maxQuantity": 89, "price": 9.9 },
        { "minQuantity": 90, "maxQuantity": 1999, "price": 8.5 },
        { "minQuantity": 2000, "maxQuantity": 4999, "price": 7.4 },
        { "minQuantity": 5000, "maxQuantity": null, "price": 6.5 }
    ],
    "moq": 10,
    "samplePrice": 22,
    "skuCount": 4,
    "certificates": [{ "name": "FCC", "type": "PRODUCT", "number": "2AP4POPENEAR-X1", "validity": "07/25/2022 - 12/30/9999" }],
    "packageSize": "15.5X9X18",
    "packageWeightKg": 0.5,
    "supplierName": "Shenzhen Alex Technology Co., Ltd.",
    "supplierBusinessType": ["Manufacturer", "Trading Company"],
    "supplierYearsOnAlibaba": 11,
    "supplierStaffCount": 142,
    "supplierFactorySizeSqm": 2400,
    "verifiedSupplier": true,
    "supplierRating": 4.5,
    "onTimeDeliveryRate": "100.0%",
    "onlineRevenue": "US$1,500,000+",
    "ordersLast6Months": 242,
    "supplierRanking": "#2 leading manufacturer in Earphone & Headphone & Accessories"
}
```

## The example: compare suppliers at your order quantity

`example.py` searches a keyword, opens every product page, and for each product works out the unit price and lead time at the quantity you actually plan to order (not the headline "from" price). It drops products whose MOQ is above your quantity and writes `alibaba_shortlist.csv` sorted by price.

```bash
pip install -r requirements.txt
APIFY_TOKEN=<YOUR_APIFY_TOKEN> python example.py
```

Real numbers from the "yoga mat" search in the 24 Oct 2026 sample, priced at 500 units:

| Unit price @ 500 | Lead time | MOQ | Years | Verified | On time | Supplier |
|---|---|---|---|---|---|---|
| $2.30 | 15 days | 2 | 19 | no | 100.0% | Sempur (Dongguan) Technology Development Co., Ltd. |
| $2.43 | n/a | 10 | 8 | no | 100.0% | Shenzhen Tengsheng Weaving Technology Co., Ltd. |
| $2.53 | 14 days | 12 | 18 | yes | 96.6% | Xi'an Leecork Co., Ltd. |
| $3.25 | 15 days | 50 | 4 | yes | 97.8% | Guangzhou Umicca Sport Products Co., Ltd. |
| $4.72 | n/a | 20 | 1 | no | 100.0% | Tianjin Xiqing District Baoya Trading Firm |
| $10.76 | 31 days | 2 | 10 | no | 100.0% | Wuxi Jstar Sports Products Co., Ltd. |
| $12.35 | 31 days | 20 | 9 | yes | 98.7% | Sansd (jiangsu) Environmental Technology Co., Ltd |

The script's last line picks the cheapest verified supplier with 5+ years on Alibaba; on this sample that was Xi'an Leecork at $2.53 ($1,265 for 500). Note how the Sansd mat lists "from $9.95" but costs $12.35 at 500 units: the ladder matters.

## Pricing and limits

- $2.50 per 1,000 products, no start fee. Removed products, invalid URLs, duplicates and failed requests are not charged.
- The long HTML description is not included (Alibaba loads it in a separate frame); specifications, highlights and certificates cover the structured part.
- Supplier capability fields appear only when the supplier shows them: staff count and factory size on about 20-35% of products, online revenue and reorder rate on about 55%.
- Prices are USD list prices as shown to a US visitor. `priceTiers` is empty when the supplier prices per SKU (each SKU then has its own `price`).
- No contact person names, phones or emails are collected.

To cover a whole category cheaply, scan search cards first with the [Alibaba search scraper](https://github.com/Rel8ble/alibaba-product-scraper-python), then send only the shortlist's URLs to this actor.

## Links

- Apify Store: https://apify.com/rel8ble/alibaba-product-details-scraper
- Tutorial on dev.to: https://dev.to/rel8ble/getting-full-alibaba-product-pages-as-json-price-tiers-skus-specs-and-the-supplier-behind-them-4i4f

## License

MIT (this example code). The actor itself is a paid Apify tool.
