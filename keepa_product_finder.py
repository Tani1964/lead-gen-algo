import os
import json
import http.client
import urllib.parse
import time
import csv
from serpapi import GoogleSearch
from dotenv import load_dotenv

# 1. SETUP
load_dotenv()
RAPID_KEY = os.getenv("RAPIDAPI_KEY")
SERP_KEY = os.getenv("SERPAPI_KEY")
# Added fallback to prevent NoneType error
API_HOST = os.getenv("API_HOST", "real-time-amazon-data.p.rapidapi.com")

SEARCH_QUERIES = [
    "under-sink organizer",
    "car trunk organizer",
    "pet grooming tool",
    "drawer dividers",
    "cable management box",
]


def get_candidates_rapid(query, page):
    """Phase 1: RapidAPI scans for Price ($20-60) and Reviews (50-300)"""
    conn = http.client.HTTPSConnection(API_HOST)
    headers = {"x-rapidapi-key": RAPID_KEY, "x-rapidapi-host": API_HOST}
    params = {
        "query": query,
        "page": str(page),
        "country": "US",
        "sort_by": "RELEVANCE",
    }

    candidates = []
    try:
        conn.request(
            "GET", f"/search?{urllib.parse.urlencode(params)}", headers=headers
        )
        res = conn.getresponse()
        if res.status != 200:
            return []
        data = json.loads(res.read().decode("utf-8"))
        products = data.get("data", {}).get("products", [])

        for p in products:
            try:
                # Clean price string to float
                price_str = (
                    str(p.get("product_price", "0")).replace("$", "").replace(",", "")
                )
                price = float(price_str)
                reviews = p.get("product_num_ratings", 0)

                # YOUR ALGORITHM FILTERS
                if (20 <= price <= 60) and (50 <= reviews <= 300):
                    candidates.append(p)
            except:
                continue
        return candidates
    except Exception as e:
        print(f"RapidAPI Error: {e}")
        return []


def verify_with_serp(asin):
    """Phase 2: SerpApi checks for 1-15 Sellers and Listing Quality"""
    params = {"engine": "amazon_product", "asin": asin, "api_key": SERP_KEY}
    try:
        search = GoogleSearch(params)
        res = search.get_dict()
        product = res.get("product_results", {})

        # Count Sellers accurately
        sellers = res.get("sellers_results", {}).get("online_sellers", [])
        seller_count = len(sellers) if sellers else 1

        # Check Quality Indicators (Opportunity Audit)
        title = product.get("title", "")
        images_count = len(product.get("images", []))

        # Opportunity logic: True if title is short OR images are few
        is_weak = len(title) < 120 or images_count < 5

        return {
            "valid_sellers": (1 <= seller_count <= 15),
            "seller_count": seller_count,
            "title": title,
            "is_weak": is_weak,
        }
    except:
        return None


def save_to_csv(leads):
    """Saves the final report to a CSV file"""
    keys = [
        "title",
        "asin",
        "price",
        "reviews",
        "sellers",
        "weak_listing",
        "alibaba",
        "url",
    ]
    filename = "sniper_leads.csv"
    with open(filename, "w", newline="", encoding="utf-8") as f:
        dict_writer = csv.DictWriter(f, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(leads)
    print(f"\n📂 Leads successfully saved to {filename}")


def run_hybrid_sniper():
    print("🎯 Starting Deep Hybrid Sniper...")
    all_raw_candidates = []

    # 1. GATHER CANDIDATES (Scanning Pages 1-3)
    for q in SEARCH_QUERIES:
        print(f"Scanning {q}...", end="\r")
        for page in range(1, 4):
            all_raw_candidates.extend(get_candidates_rapid(q, page))
            time.sleep(0.3)

    # Deduplicate by ASIN
    unique_candidates = {v["asin"]: v for v in all_raw_candidates}.values()
    cand_list = list(unique_candidates)
    print(f"\nFound {len(cand_list)} unique candidates across all pages.")

    final_leads = []
    # 2. VERIFY TOP CANDIDATES (Limited to 30 to save credits)
    for i, cand in enumerate(cand_list[:30], 1):
        asin = cand.get("asin")
        print(f"  [{i}/30] Verifying {asin}...", end="\r")
        check = verify_with_serp(asin)

        if check and check["valid_sellers"]:
            # FIXED: Alibaba URL with proper search path
            search_term = urllib.parse.quote(
                cand.get("product_title", "organizer")[:30]
            )
            alibaba_url = f"https://www.alibaba.com/products/{search_term}.html"

            final_leads.append(
                {
                    "title": check["title"][:60],
                    "asin": asin,
                    "price": cand.get("product_price"),
                    "reviews": cand.get("product_num_ratings"),
                    "sellers": check["seller_count"],
                    "weak_listing": "YES" if check["is_weak"] else "No",
                    "alibaba": alibaba_url,
                    "url": f"https://www.amazon.com/dp/{asin}",  # FIXED: Added /dp/ path
                }
            )

    # 3. FINAL REPORT
    print("\n" + "=" * 70)
    print(f"SNIPER REPORT: {len(final_leads)} VERIFIED LEADS FOUND")
    print("=" * 70)
    for i, lead in enumerate(final_leads, 1):
        print(f"{i}. {lead['title']}...")
        print(
            f"   ASIN: {lead['asin']} | Price: {lead['price']} | Reviews: {lead['reviews']}"
        )
        print(f"   Sellers: {lead['sellers']} | Weak Listing: {lead['weak_listing']}")
        print(f"   [ALIBABA PROFIT CHECK]: {lead['alibaba']}")
        print(f"   [AMAZON]: {lead['url']}\n")

    # 4. EXPORT
    if final_leads:
        save_to_csv(final_leads)


if __name__ == "__main__":
    run_hybrid_sniper()
