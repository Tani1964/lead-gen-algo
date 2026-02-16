
#!/usr/bin/env python3
"""
Lead Generation Script
Uses multiple APIs to find and aggregate business leads based on keywords
"""

import os
import re
import requests
import json
import csv
import time
from typing import List, Dict, Optional
from datetime import datetime
from bs4 import BeautifulSoup


# Load environment variables from .env file
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, will use system environment variables

# Import LEAD_CONFIG from config_example.py
try:
    from config_example import LEAD_CONFIG
except ImportError:
    LEAD_CONFIG = None


class LeadGenerator:

    def extract_contacts(self, url):
        """Extract emails and phone numbers from a website using ScraperAPI and BeautifulSoup."""
        result = self.scrape_with_scraperapi(url)
        if result and "html_length" in result and result["html_length"] > 0:
            try:
                html = self.session.get(url, timeout=30).text
            except Exception:
                html = None
            if not html:
                return {"emails": [], "phones": []}
            soup = BeautifulSoup(html, "html.parser")
            text = soup.get_text()
            emails = re.findall(r"[\w\.-]+@[\w\.-]+\.\w+", text)
            phones = re.findall(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text)
            return {"emails": emails, "phones": phones}
        return {"emails": [], "phones": []}

    def enrich_leads_with_phone(self, max_to_enrich=10):
        """For each lead with a link and no phone, try to extract phone numbers from the website.
        Only process the first `max_to_enrich` leads and skip known problematic domains."""
        print(f"\n🔎 Enriching up to {max_to_enrich} leads with phone numbers from business websites...")
        updated = 0
        processed = 0
        skip_domains = ["yelp.com", "angi.com", "bbb.org", "youtube.com"]
        for lead in self.leads:
            if processed >= max_to_enrich:
                break
            if 'phone' not in lead or not lead.get('phone'):
                url = lead.get('link')
                if url and not any(domain in url for domain in skip_domains):
                    contacts = self.extract_contacts(url)
                    if contacts['phones']:
                        lead['phone'] = contacts['phones'][0]  # Take the first found phone number
                        updated += 1
                processed += 1
        print(f"✓ Added phone numbers to {updated} leads from website scraping.")

    def __init__(self):
        """Initialize API credentials from environment variables"""
        self.serpapi_key = os.getenv("SERPAPI_KEY", "")
        self.zenserp_key = os.getenv("ZENSERP_KEY", "")
        self.dataforseo_login = os.getenv("DATAFORSEO_LOGIN", "")
        self.dataforseo_password = os.getenv("DATAFORSEO_PASSWORD", "")
        self.scraperapi_key = os.getenv("SCRAPERAPI_KEY", "")
        self.foursquare_api_key = os.getenv("FOURSQUARE_API_KEY", "")

        self.leads = []
        self.session = requests.Session()

    def search_serpapi(
        self, keyword: str, location: str = "United States"
    ) -> List[Dict]:
        """
        Search for leads using SerpAPI
        """
        if not self.serpapi_key:
            print("⚠️  SerpAPI key not configured")
            return []

        print(f"🔍 Searching SerpAPI for: {keyword}")

        params = {
            "q": keyword,
            "location": location,
            "api_key": self.serpapi_key,
            "engine": "google",
            "num": 20,
        }

        try:
            response = self.session.get(
                "https://serpapi.com/search", params=params, timeout=30
            )
            response.raise_for_status()
            data = response.json()

            leads = []

            # Extract organic results
            for result in data.get("organic_results", []):
                lead = {
                    "source": "serpapi",
                    "title": result.get("title"),
                    "link": result.get("link"),
                    "snippet": result.get("snippet"),
                    "position": result.get("position"),
                    "keyword": keyword,
                    "timestamp": datetime.now().isoformat(),
                }
                leads.append(lead)

            # Extract local results if available
            for result in data.get("local_results", {}).get("places", []):
                lead = {
                    "source": "serpapi_local",
                    "title": result.get("title"),
                    "address": result.get("address"),
                    "phone": result.get("phone"),
                    "rating": result.get("rating"),
                    "reviews": result.get("reviews"),
                    "type": result.get("type"),
                    "keyword": keyword,
                    "timestamp": datetime.now().isoformat(),
                }
                leads.append(lead)

            print(f"✓ Found {len(leads)} leads from SerpAPI")
            return leads

        except Exception as e:
            print(f"❌ SerpAPI error: {str(e)}")
            return []

    def search_zenserp(
        self, keyword: str, location: str = "United States"
    ) -> List[Dict]:
        """
        Search for leads using Zenserp
        """
        if not self.zenserp_key:
            print("⚠️  Zenserp key not configured")
            return []

        print(f"🔍 Searching Zenserp for: {keyword}")

        params = {
            "q": keyword,
            "location": location,
            "apikey": self.zenserp_key,
            "num": 20,
        }

        try:
            response = self.session.get(
                "https://app.zenserp.com/api/v2/search", params=params, timeout=30
            )
            response.raise_for_status()
            data = response.json()

            leads = []

            for result in data.get("organic", []):
                lead = {
                    "source": "zenserp",
                    "title": result.get("title"),
                    "link": result.get("url"),
                    "snippet": result.get("description"),
                    "position": result.get("position"),
                    "keyword": keyword,
                    "timestamp": datetime.now().isoformat(),
                }
                leads.append(lead)

            print(f"✓ Found {len(leads)} leads from Zenserp")
            return leads

        except Exception as e:
            print(f"❌ Zenserp error: {str(e)}")
            return []

    def search_dataforseo(self, keyword: str, location_code: int = 2840) -> List[Dict]:
        """
        Search for leads using DataForSEO
        location_code: 2840 is United States
        """
        if not self.dataforseo_login or not self.dataforseo_password:
            print("⚠️  DataForSEO credentials not configured")
            return []

        print(f"🔍 Searching DataForSEO for: {keyword}")

        post_data = [
            {
                "keyword": keyword,
                "location_code": location_code,
                "language_code": "en",
                "depth": 20,
            }
        ]

        try:
            response = self.session.post(
                "https://api.dataforseo.com/v3/serp/google/organic/live/advanced",
                json=post_data,
                auth=(self.dataforseo_login, self.dataforseo_password),
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

            leads = []

            if data.get("tasks"):
                for task in data["tasks"]:
                    if task.get("result"):
                        for item in task["result"]:
                            for result in item.get("items", []):
                                if result.get("type") == "organic":
                                    lead = {
                                        "source": "dataforseo",
                                        "title": result.get("title"),
                                        "link": result.get("url"),
                                        "snippet": result.get("description"),
                                        "position": result.get("rank_group"),
                                        "domain": result.get("domain"),
                                        "keyword": keyword,
                                        "timestamp": datetime.now().isoformat(),
                                    }
                                    leads.append(lead)

            print(f"✓ Found {len(leads)} leads from DataForSEO")
            return leads

        except Exception as e:
            print(f"❌ DataForSEO error: {str(e)}")
            return []

    def scrape_with_scraperapi(self, url: str) -> Optional[Dict]:
        """
        Scrape a URL using ScraperAPI to extract contact information
        """
        if not self.scraperapi_key:
            print("⚠️  ScraperAPI key not configured")
            return None

        params = {"api_key": self.scraperapi_key, "url": url}

        try:
            response = self.session.get(
                "https://api.scraperapi.com/", params=params, timeout=60
            )
            response.raise_for_status()

            # Simple extraction - in production, use BeautifulSoup for better parsing
            html = response.text

            result = {
                "url": url,
                "html_length": len(html),
                "scraped_at": datetime.now().isoformat(),
            }

            return result

        except Exception as e:
            print(f"❌ ScraperAPI error for {url}: {str(e)}")
            return None

    def search_openstreetmap(
        self, keyword: str, location: str = "United States"
    ) -> List[Dict]:
        """
        Search for places using OpenStreetMap Nominatim API
        """
        print(f"🔍 Searching OpenStreetMap for: {keyword}")

        params = {
            "q": f"{keyword} {location}",
            "format": "json",
            "limit": 20,
            "addressdetails": 1,
        }

        try:
            # Using Nominatim with proper user agent
            headers = {"User-Agent": "LeadGenScript/1.0"}

            response = self.session.get(
                "https://nominatim.openstreetmap.org/search",
                params=params,
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

            # Rate limiting for OSM
            time.sleep(1)

            leads = []

            for place in data:
                lead = {
                    "source": "openstreetmap",
                    "name": place.get("display_name"),
                    "type": place.get("type"),
                    "category": place.get("category"),
                    "lat": place.get("lat"),
                    "lon": place.get("lon"),
                    "address": place.get("address", {}),
                    "keyword": keyword,
                    "timestamp": datetime.now().isoformat(),
                }
                leads.append(lead)

            print(f"✓ Found {len(leads)} leads from OpenStreetMap")
            return leads

        except Exception as e:
            print(f"❌ OpenStreetMap error: {str(e)}")
            return []

    def search_foursquare(
        self, keyword: str, location: str = "United States", limit: int = 20
    ) -> List[Dict]:
        """
        Search for places using Foursquare Places API
        """
        if not self.foursquare_api_key:
            print("⚠️  Foursquare API key not configured")
            return []

        print(f"🔍 Searching Foursquare for: {keyword}")

        headers = {
            "Authorization": self.foursquare_api_key,
            "Accept": "application/json",
        }

        params = {"query": keyword, "near": location, "limit": limit}

        try:
            response = self.session.get(
                "https://api.foursquare.com/v3/places/search",
                headers=headers,
                params=params,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

            leads = []

            for place in data.get("results", []):
                lead = {
                    "source": "foursquare",
                    "name": place.get("name"),
                    "fsq_id": place.get("fsq_id"),
                    "categories": [
                        cat.get("name") for cat in place.get("categories", [])
                    ],
                    "location": place.get("location", {}),
                    "distance": place.get("distance"),
                    "keyword": keyword,
                    "timestamp": datetime.now().isoformat(),
                }
                leads.append(lead)

            print(f"✓ Found {len(leads)} leads from Foursquare")
            return leads

        except Exception as e:
            print(f"❌ Foursquare error: {str(e)}")
            return []

    def generate_leads(
        self,
        keywords: List[str],
        location: str = "United States",
        use_apis: List[str] = None,
    ) -> List[Dict]:
        """
        Generate leads from multiple APIs based on keywords

        Args:
            keywords: List of search keywords
            location: Location to search in
            use_apis: List of APIs to use. Options: ['serpapi', 'zenserp', 'dataforseo',
                     'scraperapi', 'openstreetmap', 'foursquare']
        """
        if use_apis is None:
            use_apis = [
                "serpapi",
                "zenserp",
                "dataforseo",
                "openstreetmap",
                "foursquare",
            ]

        all_leads = []

        for keyword in keywords:
            print(f"\n{'='*60}")
            print(f"Processing keyword: {keyword}")
            print(f"{'='*60}")

            if "serpapi" in use_apis:
                leads = self.search_serpapi(keyword, location)
                all_leads.extend(leads)
                time.sleep(1)  # Rate limiting

            if "zenserp" in use_apis:
                leads = self.search_zenserp(keyword, location)
                all_leads.extend(leads)
                time.sleep(1)

            if "dataforseo" in use_apis:
                leads = self.search_dataforseo(keyword)
                all_leads.extend(leads)
                time.sleep(1)

            if "openstreetmap" in use_apis:
                leads = self.search_openstreetmap(keyword, location)
                all_leads.extend(leads)
                time.sleep(1)

            if "foursquare" in use_apis:
                leads = self.search_foursquare(keyword, location)
                all_leads.extend(leads)
                time.sleep(1)

        self.leads = all_leads
        return all_leads

    def deduplicate_leads(self) -> List[Dict]:
        """
        Remove duplicate leads based on title/name and link/location
        """
        seen = set()
        unique_leads = []

        for lead in self.leads:
            # Create a unique identifier
            identifier = None

            if "link" in lead and lead["link"]:
                identifier = lead["link"]
            elif "name" in lead:
                identifier = lead["name"]
            elif "title" in lead:
                identifier = lead["title"]

            if identifier and identifier not in seen:
                seen.add(identifier)
                unique_leads.append(lead)

        print(
            f"\n📊 Deduplication: {len(self.leads)} → {len(unique_leads)} unique leads"
        )
        self.leads = unique_leads
        return unique_leads

    def export_to_json(self, filename: str = "leads.json"):
        """Export leads to JSON file"""
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.leads, f, indent=2, ensure_ascii=False)
        print(f"💾 Exported {len(self.leads)} leads to {filename}")

    def export_to_csv(self, filename: str = "leads.csv"):
        """Export leads to CSV file"""
        if not self.leads:
            print("⚠️  No leads to export")
            return

        # Get all unique keys from all leads
        all_keys = set()
        for lead in self.leads:
            all_keys.update(lead.keys())

        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=sorted(all_keys))
            writer.writeheader()

            for lead in self.leads:
                # Convert nested dicts/lists to strings
                row = {}
                for key, value in lead.items():
                    if isinstance(value, (dict, list)):
                        row[key] = json.dumps(value)
                    else:
                        row[key] = value
                writer.writerow(row)

        print(f"💾 Exported {len(self.leads)} leads to {filename}")

    def print_summary(self):
        """Print a summary of generated leads"""
        if not self.leads:
            print("\n📊 No leads generated")
            return

        print(f"\n{'='*60}")
        print("📊 LEAD GENERATION SUMMARY")
        print(f"{'='*60}")
        print(f"Total leads: {len(self.leads)}")

        # Count by source
        sources = {}
        for lead in self.leads:
            source = lead.get("source", "unknown")
            sources[source] = sources.get(source, 0) + 1

        print("\nBy source:")
        for source, count in sorted(sources.items()):
            print(f"  • {source}: {count}")

        # Count by keyword
        keywords = {}
        for lead in self.leads:
            keyword = lead.get("keyword", "unknown")
            keywords[keyword] = keywords.get(keyword, 0) + 1

        print("\nBy keyword:")
        for keyword, count in sorted(keywords.items()):
            print(f"  • {keyword}: {count}")


def main():
    """Main function to run the lead generation script"""
    # Entry point for the script
    print(
        """
    ╔═══════════════════════════════════════════════════════════╗
    ║         LEAD GENERATION SCRIPT v1.0                       ║
    ║         Multi-API Lead Finder                             ║
    ╚═══════════════════════════════════════════════════════════╝
    """
    )

    # Initialize the lead generator
    generator = LeadGenerator()

    # Use LEAD_CONFIG if available, otherwise fallback to hardcoded values
    if LEAD_CONFIG:
        keywords = LEAD_CONFIG.get("keywords", [])
        location = LEAD_CONFIG.get("location", "United States")
        apis_to_use = LEAD_CONFIG.get(
            "apis", ["openstreetmap", "serpapi", "zenserp", "dataforseo", "foursquare"]
        )
    else:
        keywords = [
            "plumbers near me",
            "digital marketing agency",
            "real estate agents",
            "restaurants",
            "coffee shops",
        ]
        location = "New York, NY"
        apis_to_use = [
            "openstreetmap",
            "serpapi",
            "zenserp",
            "dataforseo",
            "foursquare",
        ]

    print(f"🎯 Keywords: {', '.join(keywords)}")
    print(f"📍 Location: {location}")
    print(f"🔧 APIs: {', '.join(apis_to_use)}\n")

    # Generate leads
    generator.generate_leads(keywords=keywords, location=location, use_apis=apis_to_use)

    # Deduplicate
    generator.deduplicate_leads()

    # Enrich leads with phone numbers from business websites
    generator.enrich_leads_with_phone(max_to_enrich=10)

    # Print summary
    generator.print_summary()

    # Export results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    generator.export_to_json(f"leads_{timestamp}.json")
    generator.export_to_csv(f"leads_{timestamp}.csv")

    print("\n✅ Lead generation complete!")


if __name__ == "__main__":
    main()
