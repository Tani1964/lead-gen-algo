"""
============================================================
  Amazon Product Opportunity Finder — Keepa-Powered
  Targets: Home & Kitchen | Pet Supplies | Tools & Home
           Improvement | Automotive
============================================================
Requirements:
    pip install keepa requests pandas tabulate colorama

Usage:
    1. Add your Keepa API key to KEEPA_API_KEY below (or set
       the environment variable KEEPA_API_KEY).
    2. Optionally add a SerpAPI key for Alibaba/AliExpress
       supplier price lookups (SERP_API_KEY).
    3. Run:  python keepa_product_researcher.py
    4. Results are saved to  product_opportunities.csv
============================================================
"""

import os
import time
import statistics
import logging
from dataclasses import dataclass, field, asdict
from typing import Optional
from pathlib import Path

from dotenv import load_dotenv  # pip install python-dotenv
import keepa as keepa  # pip install keepa
import pandas as pd
import requests
from colorama import Fore, Style, init as colorama_init

colorama_init(autoreset=True)
logging.basicConfig(level=logging.INFO, format="%(levelname)s │ %(message)s")
log = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# 🔑  Load API Keys from .env file
# ─────────────────────────────────────────────
_env_path = Path(__file__).parent / ".env"
if _env_path.exists():
    load_dotenv(dotenv_path=_env_path)
    log.info(f"Loaded .env from {_env_path}")
else:
    load_dotenv()  # fallback: look in cwd / system env
    log.warning(".env file not found — falling back to system environment variables")

KEEPA_API_KEY: str = os.getenv("KEEPA_API_KEY", "")
SERP_API_KEY: str = os.getenv("SERP_API_KEY", "")  # optional, for supplier prices

if not KEEPA_API_KEY:
    raise EnvironmentError(
        "KEEPA_API_KEY is not set.\n"
        "Create a .env file in the same folder as this script with:\n\n"
        "  KEEPA_API_KEY=your_key_here\n"
        "  SERP_API_KEY=your_key_here   # optional\n"
    )

# ─────────────────────────────────────────────
# 🎛️  Filter Parameters
# ─────────────────────────────────────────────
PRICE_MIN = 20.0  # USD
PRICE_MAX = 60.0
RANK_MIN = 200
RANK_MAX = 2_000
REVIEWS_MIN = 50
REVIEWS_MAX = 300
SELLERS_MIN = 3
SELLERS_MAX = 15
PROFIT_MIN = 10.0
PROFIT_MAX = 20.0
TOP_N = 20  # Final list size

# ─────────────────────────────────────────────
# 🗂️  Target Categories  (Keepa node IDs)
# ─────────────────────────────────────────────
CATEGORIES = {
    "Home & Kitchen": 1055398,
    "Pet Supplies": 2619533011,
    "Tools & Home Improvement": 228013,
    "Automotive": 15684181,
}

# ─────────────────────────────────────────────
# 🔍  Seed keywords for Best-Seller search
# ─────────────────────────────────────────────
SEED_KEYWORDS = [
    "under sink organizer",
    "car trunk organizer",
    "pet grooming tool",
    "drawer divider",
    "cable management box",
    "kitchen cabinet organizer",
    "shower caddy",
    "garage storage rack",
    "dog brush deshedding",
    "tool storage organizer",
    "car seat back organizer",
    "bathroom counter organizer",
    "pantry shelf organizer",
    "pet hair remover",
    "utility hook wall mount",
]


# ─────────────────────────────────────────────────────────────────────────────
# 📦  Data Model
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class Product:
    asin: str = ""
    title: str = ""
    category: str = ""
    price: float = 0.0
    sales_rank: int = 0
    review_count: int = 0
    rating: float = 0.0
    seller_count: int = 0
    brand: str = ""
    image_count: int = 0
    # Keepa trend signals
    rank_downward_spikes: int = 0  # # of sudden rank-drop events (sales bursts)
    price_trend: str = ""  # "stable" | "increasing" | "decreasing"
    # Supplier / profit
    supplier_price: float = 0.0
    estimated_profit: float = 0.0
    profit_margin_pct: float = 0.0
    # Listing quality score (0–100, lower = more opportunity)
    listing_quality_score: int = 100
    quality_flags: list = field(default_factory=list)
    # Composite opportunity score (higher = better)
    opportunity_score: float = 0.0
    url: str = ""


# ─────────────────────────────────────────────────────────────────────────────
# 🔌  Keepa helpers
# ─────────────────────────────────────────────────────────────────────────────
class KeepaClient:
    """Thin wrapper around the `keepa` library."""

    KEEPA_TIME_OFFSET = 21564000  # minutes since epoch to keepa epoch

    def __init__(self, api_key: str):
        self.api = keepa.Keepa(api_key)
        log.info(f"Keepa tokens remaining: {self.api.tokens_left}")

    # ------------------------------------------------------------------
    def search_products(
        self, keyword: str, category_node: int, max_results: int = 50
    ) -> list[dict]:
        """Run a Keepa product search and return raw product dicts."""
        try:
            params = {
                "search": keyword,
                "domain": 1,  # amazon.com
                "category": category_node,
                "range": {
                    "current_SALES_RANK_FLAT": [RANK_MIN, RANK_MAX],
                    "current_AMAZON": [int(PRICE_MIN * 100), int(PRICE_MAX * 100)],
                    "current_COUNT_REVIEWS": [REVIEWS_MIN, REVIEWS_MAX],
                },
                "sort": [["current_SALES_RANK_FLAT", "asc"]],
                "perPage": max_results,
            }
            result = self.api.product_finder(params)
            if result:
                return result
        except Exception as exc:
            log.warning(f"search_products({keyword}): {exc}")
        return []

    # ------------------------------------------------------------------
    def get_product_details(self, asins: list[str]) -> list[dict]:
        """Fetch full Keepa product data for a list of ASINs."""
        if not asins:
            return []
        try:
            products = self.api.query(
                asins,
                domain=1,
                history=True,
                offers=20,
                update=0,
            )
            return products if products else []
        except Exception as exc:
            log.warning(f"get_product_details: {exc}")
            return []

    # ------------------------------------------------------------------
    @staticmethod
    def extract_price_history(product: dict) -> list[float]:
        """Return list of Amazon prices (USD) from Keepa history array."""
        csv = product.get("csv", [])
        # csv[1] is AMAZON price track; values are in cents, -1 = unavailable
        if len(csv) > 1 and csv[1]:
            raw = csv[1]
            # Keepa interleaves [time, value, time, value ...]
            values = [raw[i] / 100.0 for i in range(1, len(raw), 2) if raw[i] > 0]
            return values
        return []

    # ------------------------------------------------------------------
    @staticmethod
    def extract_rank_history(product: dict) -> list[int]:
        """Return list of sales ranks from Keepa history."""
        csv = product.get("csv", [])
        if len(csv) > 3 and csv[3]:
            raw = csv[3]
            values = [raw[i] for i in range(1, len(raw), 2) if raw[i] > 0]
            return values
        return []

    # ------------------------------------------------------------------
    @staticmethod
    def detect_downward_spikes(
        rank_history: list[int], threshold_pct: float = 0.40
    ) -> int:
        """
        Count events where the rank suddenly drops ≥ threshold_pct below
        the rolling median (a proxy for a sales burst).
        """
        if len(rank_history) < 10:
            return 0
        spikes = 0
        window = 10
        for i in range(window, len(rank_history)):
            window_median = statistics.median(rank_history[i - window : i])
            current = rank_history[i]
            # rank DROP = rank number decreases = better sales
            if window_median > 0 and current < window_median * (1 - threshold_pct):
                spikes += 1
        return spikes

    # ------------------------------------------------------------------
    @staticmethod
    def analyze_price_trend(price_history: list[float]) -> str:
        """Return 'increasing', 'stable', or 'decreasing'."""
        if len(price_history) < 6:
            return "stable"
        first_half = statistics.mean(price_history[: len(price_history) // 2])
        second_half = statistics.mean(price_history[len(price_history) // 2 :])
        diff_pct = (second_half - first_half) / first_half if first_half else 0
        if diff_pct > 0.03:
            return "increasing"
        if diff_pct < -0.03:
            return "decreasing"
        return "stable"

    # ------------------------------------------------------------------
    @staticmethod
    def count_offer_sellers(product: dict) -> int:
        """
        Approximate third-party seller count from Keepa's offers array
        (mirrors the 'Other Sellers on Amazon' box).
        """
        offers = product.get("offers", []) or []
        third_party = [o for o in offers if o.get("isFBA") or o.get("isMarketplace")]
        return len(third_party)


# ─────────────────────────────────────────────────────────────────────────────
# 💰  Supplier price lookup  (SerpAPI → Google Shopping)
# ─────────────────────────────────────────────────────────────────────────────
class SupplierPricer:
    ALIBABA_MARKUP = 1.25  # assume 25 % shipping / import overhead
    ALIEXPRESS_MARKUP = 1.15

    def __init__(self, serp_key: str = ""):
        self.serp_key = serp_key

    def get_supplier_price(self, title: str) -> float:
        """
        Try SerpAPI Google Shopping for supplier price.
        Falls back to a heuristic (30–40 % of Amazon price) if no key.
        """
        if self.serp_key:
            try:
                return self._serp_lookup(title)
            except Exception as exc:
                log.debug(f"SerpAPI lookup failed: {exc}")
        # Heuristic fallback
        return 0.0  # caller will use heuristic

    def _serp_lookup(self, query: str) -> float:
        url = "https://serpapi.com/search"
        params = {
            "engine": "google_shopping",
            "q": query + " wholesale alibaba",
            "api_key": self.serp_key,
            "num": 5,
        }
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        results = resp.json().get("shopping_results", [])
        prices = []
        for r in results:
            try:
                p = float(str(r.get("price", "0")).replace("$", "").replace(",", ""))
                if 0.5 < p < 40:
                    prices.append(p * self.ALIBABA_MARKUP)
            except ValueError:
                pass
        return statistics.median(prices) if prices else 0.0

    @staticmethod
    def heuristic_supplier_price(amazon_price: float) -> float:
        """
        Without live data: Alibaba factory price is typically
        20–35 % of Amazon retail for these product categories.
        Use 30 % as a conservative estimate.
        """
        return round(amazon_price * 0.30, 2)


# ─────────────────────────────────────────────────────────────────────────────
# 🖼️  Listing Quality Analyzer
# ─────────────────────────────────────────────────────────────────────────────
class ListingQualityAnalyzer:

    @staticmethod
    def analyze(product_raw: dict) -> tuple[int, list[str]]:
        """
        Returns (quality_score 0-100, [flag strings]).
        Lower score = weaker listing = more opportunity for YOU.
        """
        flags = []
        penalty = 0  # accumulate deductions from 100

        # ── Image count ──────────────────────────────────────────────
        images = product_raw.get("imagesCSV", "") or ""
        img_count = len([x for x in images.split(",") if x.strip()])
        if img_count <= 3:
            flags.append(f"⚠ Only {img_count} image(s) — basic listing")
            penalty += 25
        elif img_count <= 5:
            flags.append(f"ℹ {img_count} images — few lifestyle photos")
            penalty += 10

        # ── Title quality ─────────────────────────────────────────────
        title = product_raw.get("title", "") or ""
        if len(title) < 60:
            flags.append("⚠ Short title — likely keyword-poor")
            penalty += 20
        if title == title.upper() and len(title) > 10:
            flags.append("⚠ ALL-CAPS title — unprofessional")
            penalty += 10

        # ── Description / bullet points ───────────────────────────────
        features = product_raw.get("features", []) or []
        if len(features) < 3:
            flags.append(f"⚠ Only {len(features)} bullet point(s) — weak copy")
            penalty += 20
        desc = product_raw.get("description", "") or ""
        if len(desc) < 200:
            flags.append("⚠ Thin product description")
            penalty += 15

        # ── Brand signal ──────────────────────────────────────────────
        brand = product_raw.get("brand", "") or ""
        if not brand or brand.lower() in ("generic", "unbranded", "n/a", ""):
            flags.append("ℹ Generic / no brand — private label opportunity")
            penalty += 5

        quality_score = max(0, 100 - penalty)
        return quality_score, flags


# ─────────────────────────────────────────────────────────────────────────────
# 🧮  Opportunity Scorer
# ─────────────────────────────────────────────────────────────────────────────
def compute_opportunity_score(p: Product) -> float:
    """
    Composite score weighing:
      • Profit margin          (higher = better)
      • Sales rank             (lower = better, inverted)
      • Review count           (fewer = less competition)
      • Seller count           (within sweet spot 3–15)
      • Rank downward spikes   (more = proven demand)
      • Listing quality        (weaker listing = more upside)
      • Price trend            (stable/up = safer)
    """
    score = 0.0

    # Profit margin (0–20 pts)
    if p.price > 0:
        margin = (p.estimated_profit / p.price) * 100
        score += min(20, margin)

    # Rank (0–20 pts) — rank 200 is best, 2000 worst
    rank_score = 20 * (1 - (p.sales_rank - RANK_MIN) / (RANK_MAX - RANK_MIN))
    score += max(0, rank_score)

    # Reviews (0–15 pts) — fewer reviews = less entrenched competition
    rev_score = 15 * (1 - (p.review_count - REVIEWS_MIN) / (REVIEWS_MAX - REVIEWS_MIN))
    score += max(0, rev_score)

    # Seller count in sweet spot (0–10 pts)
    if SELLERS_MIN <= p.seller_count <= SELLERS_MAX:
        score += 10
    elif p.seller_count < SELLERS_MIN:
        score += 4  # maybe too niche
    else:
        score += 2  # overcrowded

    # Rank spikes = proven demand (0–15 pts)
    score += min(15, p.rank_downward_spikes * 3)

    # Listing weakness = your opportunity (0–10 pts)
    listing_opp = (100 - p.listing_quality_score) / 10
    score += min(10, listing_opp)

    # Price trend (0–10 pts)
    if p.price_trend == "increasing":
        score += 10
    elif p.price_trend == "stable":
        score += 7
    else:
        score += 2

    return round(score, 2)


# ─────────────────────────────────────────────────────────────────────────────
# 🚀  Main Pipeline
# ─────────────────────────────────────────────────────────────────────────────
class ProductResearcher:

    def __init__(self):
        if KEEPA_API_KEY == "YOUR_KEEPA_API_KEY_HERE":
            raise ValueError(
                "Please set your Keepa API key in the script or via the "
                "environment variable KEEPA_API_KEY."
            )
        self.keepa = KeepaClient(KEEPA_API_KEY)
        self.pricer = SupplierPricer(SERP_API_KEY)
        self.analyzer = ListingQualityAnalyzer()

    # ------------------------------------------------------------------
    def run(self) -> list[Product]:
        log.info("═" * 60)
        log.info("  Amazon Product Opportunity Finder — Starting")
        log.info("═" * 60)

        candidate_asins: set[str] = set()

        # Step 1 ─ Collect ASINs via keyword × category search
        for cat_name, cat_node in CATEGORIES.items():
            for keyword in SEED_KEYWORDS:
                log.info(f"Searching [{cat_name}] ← '{keyword}'")
                asins = self.keepa.search_products(keyword, cat_node, max_results=30)
                candidate_asins.update(asins)
                time.sleep(0.5)  # be kind to rate limits

        log.info(f"\nTotal unique ASINs found: {len(candidate_asins)}")

        # Step 2 ─ Fetch full details in batches of 10
        all_products: list[Product] = []
        asin_list = list(candidate_asins)
        batch_size = 10
        for i in range(0, len(asin_list), batch_size):
            batch = asin_list[i : i + batch_size]
            log.info(
                f"Fetching details batch {i // batch_size + 1} "
                f"({len(batch)} ASINs) …"
            )
            raw_products = self.keepa.get_product_details(batch)
            for raw in raw_products:
                p = self._parse_product(raw)
                if p:
                    all_products.append(p)
            time.sleep(1)

        log.info(f"\nProducts passing all filters: {len(all_products)}")

        # Step 3 ─ Score and rank
        for p in all_products:
            p.opportunity_score = compute_opportunity_score(p)

        all_products.sort(key=lambda x: x.opportunity_score, reverse=True)
        top = all_products[:TOP_N]

        return top

    # ------------------------------------------------------------------
    def _parse_product(self, raw: dict) -> Optional[Product]:
        """Extract, filter, and enrich a single Keepa product dict."""

        # ── Basic fields ──────────────────────────────────────────────
        asin = raw.get("asin", "")
        title = raw.get("title", "") or ""
        brand = raw.get("brand", "") or ""

        # Price (Keepa stores in cents)
        price_cents = raw.get("stats", {}).get("current", [None] * 20)
        amazon_price = 0.0
        try:
            # stats.current[1] = AMAZON price
            cp = raw["stats"]["current"][1]
            amazon_price = cp / 100.0 if cp and cp > 0 else 0.0
        except (KeyError, IndexError, TypeError):
            pass

        if not (PRICE_MIN <= amazon_price <= PRICE_MAX):
            return None

        # Sales rank
        try:
            rank = raw["stats"]["current"][3]
            if rank is None or rank < 0:
                rank = 0
        except (KeyError, IndexError):
            rank = 0
        if not (RANK_MIN <= rank <= RANK_MAX):
            return None

        # Review count
        review_count = raw.get("stats", {}).get("current", [None] * 20)
        try:
            rc = raw["stats"]["current"][16]
            review_count = rc if rc and rc > 0 else 0
        except (KeyError, IndexError, TypeError):
            review_count = 0
        if not (REVIEWS_MIN <= review_count <= REVIEWS_MAX):
            return None

        # Rating
        try:
            rating = raw["stats"]["current"][17] / 10.0
        except (KeyError, IndexError, TypeError):
            rating = 0.0

        # ── Keepa history signals ─────────────────────────────────────
        rank_history = self.keepa.extract_rank_history(raw)
        price_history = self.keepa.extract_price_history(raw)
        spikes = self.keepa.detect_downward_spikes(rank_history)
        price_trend = self.keepa.analyze_price_trend(price_history)

        # Only keep stable/increasing prices
        if price_trend == "decreasing":
            return None

        # ── Seller count ──────────────────────────────────────────────
        seller_count = self.keepa.count_offer_sellers(raw)
        if not (SELLERS_MIN <= seller_count <= SELLERS_MAX):
            return None

        # ── Category label ────────────────────────────────────────────
        cat_id = (
            raw.get("categoryTree", [{}])[-1].get("catId", 0)
            if raw.get("categoryTree")
            else 0
        )
        category = next(
            (name for name, nid in CATEGORIES.items() if nid == cat_id), "Other"
        )

        # ── Listing quality ───────────────────────────────────────────
        quality_score, quality_flags = self.analyzer.analyze(raw)

        # ── Supplier / profit ─────────────────────────────────────────
        supplier_price = self.pricer.get_supplier_price(title[:80])
        if supplier_price == 0.0:
            supplier_price = SupplierPricer.heuristic_supplier_price(amazon_price)

        # Amazon FBA fee estimate (~15 % referral + ~$3.5 fulfillment)
        fba_fees = amazon_price * 0.15 + 3.50
        estimated_profit = amazon_price - supplier_price - fba_fees
        if not (PROFIT_MIN <= estimated_profit <= PROFIT_MAX):
            return None

        profit_margin_pct = estimated_profit / amazon_price * 100 if amazon_price else 0

        # ── Image count ───────────────────────────────────────────────
        images = raw.get("imagesCSV", "") or ""
        img_count = len([x for x in images.split(",") if x.strip()])

        url = f"https://www.amazon.com/dp/{asin}"

        return Product(
            asin=asin,
            title=title[:120],
            category=category,
            price=amazon_price,
            sales_rank=rank,
            review_count=review_count,
            rating=rating,
            seller_count=seller_count,
            brand=brand,
            image_count=img_count,
            rank_downward_spikes=spikes,
            price_trend=price_trend,
            supplier_price=supplier_price,
            estimated_profit=round(estimated_profit, 2),
            profit_margin_pct=round(profit_margin_pct, 1),
            listing_quality_score=quality_score,
            quality_flags=quality_flags,
            url=url,
        )


# ─────────────────────────────────────────────────────────────────────────────
# 📊  Output helpers
# ─────────────────────────────────────────────────────────────────────────────
def print_results(products: list[Product]) -> None:
    print(f"\n{Fore.CYAN}{'═' * 90}")
    print(f"  🏆  TOP {len(products)} AMAZON PRODUCT OPPORTUNITIES")
    print(f"{'═' * 90}{Style.RESET_ALL}\n")

    for rank, p in enumerate(products, 1):
        trend_icon = {"increasing": "📈", "stable": "➡️", "decreasing": "📉"}.get(
            p.price_trend, "➡️"
        )
        print(f"{Fore.YELLOW}#{rank:>2}  {p.title[:80]}{Style.RESET_ALL}")
        print(
            f"     ASIN: {p.asin}  │  Category: {p.category}  │  Brand: {p.brand or 'Generic'}"
        )
        print(
            f"     💲 Amazon: ${p.price:.2f}  │  Supplier: ${p.supplier_price:.2f}"
            f"  │  Est. Profit: {Fore.GREEN}${p.estimated_profit:.2f}"
            f" ({p.profit_margin_pct:.0f}%){Style.RESET_ALL}"
        )
        print(
            f"     📦 Rank: #{p.sales_rank:,}  │  ⭐ Reviews: {p.review_count}"
            f"  │  👥 Sellers: {p.seller_count}"
        )
        print(
            f"     {trend_icon} Price Trend: {p.price_trend.capitalize()}"
            f"  │  📉 Demand Spikes: {p.rank_downward_spikes}"
            f"  │  🖼 Images: {p.image_count}"
        )
        print(
            f"     📋 Listing Score: {p.listing_quality_score}/100"
            f"  │  🎯 Opportunity Score: {Fore.CYAN}{p.opportunity_score}{Style.RESET_ALL}"
        )
        if p.quality_flags:
            for flag in p.quality_flags:
                print(f"        {flag}")
        print(f"     🔗 {p.url}")
        print()


def save_csv(products: list[Product], path: str = "product_opportunities.csv") -> None:
    rows = []
    for p in products:
        d = asdict(p)
        d["quality_flags"] = " | ".join(p.quality_flags)
        rows.append(d)
    df = pd.DataFrame(rows)
    df.to_csv(path, index=False)
    log.info(f"Results saved → {path}")


# ─────────────────────────────────────────────────────────────────────────────
# ▶️  Entry point
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    researcher = ProductResearcher()
    top_products = researcher.run()

    if top_products:
        print_results(top_products)
        save_csv(top_products, "/mnt/user-data/outputs/product_opportunities.csv")
    else:
        print(
            Fore.RED + "\n⚠  No products matched all criteria. "
            "Try relaxing the filters or adding more keywords." + Style.RESET_ALL
        )
