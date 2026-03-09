#!/usr/bin/env python3
"""
Austin Area Lead Generation Script
Searches for leads in specific Austin-area cities:
Pflugerville, Hutto, Taylor, Manor, Elgin, Georgetown, Austin
"""

import sys
import os

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from lead_gen_script import LeadGenerator
from datetime import datetime


def generate_austin_area_leads(keywords, cities=None):
    """
    Generate leads for specific Austin-area cities
    
    Args:
        keywords: List of business types to search for
        cities: List of cities (defaults to Austin area)
    """
    
    # Default Austin-area cities
    if cities is None:
        cities = [
            "Pflugerville, TX",
            "Hutto, TX",
            "Taylor, TX",
            "Manor, TX",
            "Elgin, TX",
            "Georgetown, TX",
            "Austin, TX"
        ]
    
    # APIs to use (only working ones)
    apis = ['serpapi', 'openstreetmap']
    
    # Add foursquare if key is available and working
    if os.getenv('FOURSQUARE_API_KEY'):
        apis.append('foursquare')
    
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║         AUSTIN AREA LEAD GENERATION                       ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    print(f"🎯 Keywords: {', '.join(keywords)}")
    print(f"📍 Cities: {', '.join(cities)}")
    print(f"🔧 APIs: {', '.join(apis)}\n")
    
    generator = LeadGenerator()
    all_leads = []
    
    # Search each city separately
    for city in cities:
        print(f"\n{'='*60}")
        print(f"📍 Searching in: {city}")
        print(f"{'='*60}\n")
        
        # Search for all keywords in this city
        leads = generator.generate_leads(
            keywords=keywords,
            location=city,
            use_apis=apis
        )
        
        all_leads.extend(leads)
    
    # Update generator's leads list
    generator.leads = all_leads
    
    # Remove duplicates
    generator.deduplicate_leads()
    
    # Print summary
    generator.print_summary()
    
    # Export with timestamp and city info
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_file = f"austin_area_leads_{timestamp}.json"
    csv_file = f"austin_area_leads_{timestamp}.csv"
    
    generator.export_to_json(json_file)
    generator.export_to_csv(csv_file)
    
    print(f"\n📊 Total unique leads collected: {len(generator.leads)}")
    
    # Show breakdown by city
    print("\n📍 Leads by city:")
    city_count = {}
    for lead in generator.leads:
        lead_city = "Unknown"
        # Try to extract city from various fields
        if 'address' in lead and lead['address']:
            if isinstance(lead['address'], dict):
                lead_city = lead['address'].get('city', 'Unknown')
            else:
                # Try to find city in address string
                for city in cities:
                    city_name = city.split(',')[0]
                    if city_name.lower() in str(lead['address']).lower():
                        lead_city = city_name
                        break
        
        city_count[lead_city] = city_count.get(lead_city, 0) + 1
    
    for city, count in sorted(city_count.items(), key=lambda x: x[1], reverse=True):
        print(f"  • {city}: {count}")
    
    return generator.leads


def main():
    """Main function with example searches"""
    
    # CUSTOMIZE THESE KEYWORDS FOR YOUR NEEDS
    keywords = [
        "roofing companies",
        "roofing contractors",
        "roofers"
    ]
    
    # You can customize cities or use default Austin area
    cities = [
        "Pflugerville, TX",
        "Hutto, TX",
        "Taylor, TX",
        "Manor, TX",
        "Elgin, TX",
        "Georgetown, TX",
        "Austin, TX"
    ]
    
    # Generate leads
    leads = generate_austin_area_leads(keywords, cities)
    
    print(f"\n✅ Lead generation complete! Found {len(leads)} leads.")


# Additional examples for different industries
def example_home_services():
    """Generate leads for home service businesses"""
    keywords = [
        "plumbers",
        "electricians",
        "HVAC contractors",
        "general contractors"
    ]
    return generate_austin_area_leads(keywords)


def example_restaurants():
    """Generate leads for restaurants and food businesses"""
    keywords = [
        "restaurants",
        "cafes",
        "food trucks",
        "catering"
    ]
    return generate_austin_area_leads(keywords)


def example_healthcare():
    """Generate leads for healthcare providers"""
    keywords = [
        "dentists",
        "chiropractors",
        "urgent care",
        "medical clinics"
    ]
    return generate_austin_area_leads(keywords)


def example_professional_services():
    """Generate leads for professional services"""
    keywords = [
        "law firms",
        "accounting firms",
        "real estate agents",
        "insurance agents"
    ]
    return generate_austin_area_leads(keywords)


if __name__ == "__main__":
    # Check if user wants to run a specific example
    if len(sys.argv) > 1:
        example = sys.argv[1].lower()
        
        examples = {
            'roofing': main,
            'home': example_home_services,
            'restaurants': example_restaurants,
            'healthcare': example_healthcare,
            'professional': example_professional_services
        }
        
        if example in examples:
            print(f"\nRunning: {example} example\n")
            examples[example]()
        else:
            print(f"Unknown example: {example}")
            print(f"Available: {', '.join(examples.keys())}")
    else:
        # Default: run main roofing search
        main()
