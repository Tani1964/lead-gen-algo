#!/usr/bin/env python3
"""
Advanced usage examples for the lead generation script
Run specific functions based on your needs
"""

import sys
import os

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, will use system environment variables

from lead_gen_script import LeadGenerator


def example_basic_search():
    """Basic search with default settings"""
    print("=" * 60)
    print("EXAMPLE 1: Basic Search")
    print("=" * 60)
    
    gen = LeadGenerator()
    
    # Simple search with OpenStreetMap (no API key needed)
    keywords = ["coffee shops"]
    location = "Portland, OR"
    
    leads = gen.generate_leads(
        keywords=keywords,
        location=location,
        use_apis=['openstreetmap']
    )
    
    gen.deduplicate_leads()
    gen.print_summary()
    gen.export_to_csv("example_basic_leads.csv")


def example_multi_keyword():
    """Search with multiple keywords across different industries"""
    print("=" * 60)
    print("EXAMPLE 2: Multi-Keyword Search")
    print("=" * 60)
    
    gen = LeadGenerator()
    
    keywords = [
        "real estate agents",
        "property management",
        "mortgage brokers"
    ]
    location = "Miami, FL"
    
    # Using free APIs
    apis = ['openstreetmap']
    
    # Add Foursquare if API key is available
    if os.getenv('FOURSQUARE_API_KEY'):
        apis.append('foursquare')
    
    leads = gen.generate_leads(keywords, location, apis)
    gen.deduplicate_leads()
    gen.print_summary()
    gen.export_to_json("real_estate_leads.json")


def example_location_comparison():
    """Compare the same business type across multiple locations"""
    print("=" * 60)
    print("EXAMPLE 3: Location Comparison")
    print("=" * 60)
    
    gen = LeadGenerator()
    keyword = "pizza restaurants"
    
    locations = [
        "New York, NY",
        "Chicago, IL",
        "Boston, MA"
    ]
    
    all_leads = []
    
    for location in locations:
        print(f"\nSearching in {location}...")
        leads = gen.search_openstreetmap(keyword, location)
        all_leads.extend(leads)
    
    gen.leads = all_leads
    gen.deduplicate_leads()
    gen.print_summary()
    gen.export_to_csv("pizza_comparison.csv")


def example_api_comparison():
    """Compare results from different APIs for the same search"""
    print("=" * 60)
    print("EXAMPLE 4: API Comparison")
    print("=" * 60)
    
    gen = LeadGenerator()
    keyword = "restaurants"
    location = "Seattle, WA"
    
    # Test each API separately
    apis = ['openstreetmap', 'serpapi', 'foursquare', 'zenserp']
    
    for api in apis:
        print(f"\n--- Testing {api.upper()} ---")
        leads = gen.generate_leads([keyword], location, use_apis=[api])
        print(f"Found {len(leads)} leads from {api}")
    
    gen.print_summary()


def example_foursquare_specific():
    """Foursquare-specific search with categories"""
    print("=" * 60)
    print("EXAMPLE 5: Foursquare Places Search")
    print("=" * 60)
    
    if not os.getenv('FOURSQUARE_API_KEY'):
        print("⚠️  Set FOURSQUARE_API_KEY environment variable to run this example")
        return
    
    gen = LeadGenerator()
    
    # Different types of places
    queries = [
        "coffee shop",
        "coworking space",
        "gym",
        "bookstore"
    ]
    
    location = "San Francisco, CA"
    
    for query in queries:
        leads = gen.search_foursquare(query, location, limit=10)
        print(f"\n{query}: {len(leads)} results")
    
    gen.print_summary()
    gen.export_to_json("foursquare_places.json")


def example_serpapi_local():
    """SerpAPI focused on local business results"""
    print("=" * 60)
    print("EXAMPLE 6: SerpAPI Local Business Search")
    print("=" * 60)
    
    if not os.getenv('SERPAPI_KEY'):
        print("⚠️  Set SERPAPI_KEY environment variable to run this example")
        return
    
    gen = LeadGenerator()
    
    # Search for local services
    keywords = [
        "plumber near me",
        "electrician near me",
        "HVAC repair near me"
    ]
    location = "Austin, TX"
    
    leads = gen.generate_leads(keywords, location, use_apis=['serpapi'])
    gen.deduplicate_leads()
    gen.print_summary()
    gen.export_to_csv("local_services.csv")


def example_industry_specific():
    """Industry-specific lead generation with custom filtering"""
    print("=" * 60)
    print("EXAMPLE 7: Industry-Specific (Healthcare)")
    print("=" * 60)
    
    gen = LeadGenerator()
    
    # Healthcare providers
    keywords = [
        "dentist",
        "dental clinic",
        "orthodontist",
        "cosmetic dentistry"
    ]
    location = "Los Angeles, CA"
    
    leads = gen.generate_leads(
        keywords=keywords,
        location=location,
        use_apis=['openstreetmap', 'foursquare']
    )
    
    gen.deduplicate_leads()
    
    # Filter for specific criteria (example)
    filtered_leads = []
    for lead in gen.leads:
        # You can add custom filtering logic here
        # For example, filter by rating if available
        if 'rating' in lead:
            if lead['rating'] and float(lead.get('rating', 0)) >= 4.0:
                filtered_leads.append(lead)
        else:
            filtered_leads.append(lead)
    
    print(f"\nFiltered: {len(gen.leads)} → {len(filtered_leads)} leads")
    gen.leads = filtered_leads
    gen.export_to_csv("healthcare_leads.csv")


def example_export_formats():
    """Demonstrate different export options"""
    print("=" * 60)
    print("EXAMPLE 8: Export Formats")
    print("=" * 60)
    
    gen = LeadGenerator()
    
    # Quick search
    leads = gen.search_openstreetmap("bakery", "Portland, OR")
    gen.leads = leads
    
    # Export in different formats
    gen.export_to_json("bakeries.json")
    gen.export_to_csv("bakeries.csv")
    
    # Show sample of data
    if gen.leads:
        print("\nSample lead data:")
        import json
        print(json.dumps(gen.leads[0], indent=2))


def example_batch_processing():
    """Process multiple searches and combine results"""
    print("=" * 60)
    print("EXAMPLE 9: Batch Processing")
    print("=" * 60)
    
    gen = LeadGenerator()
    
    # Define multiple search configurations
    searches = [
        {"keywords": ["italian restaurant"], "location": "Boston, MA"},
        {"keywords": ["mexican restaurant"], "location": "Boston, MA"},
        {"keywords": ["asian restaurant"], "location": "Boston, MA"},
    ]
    
    all_leads = []
    
    for search in searches:
        print(f"\nProcessing: {search['keywords']} in {search['location']}")
        leads = gen.generate_leads(
            keywords=search['keywords'],
            location=search['location'],
            use_apis=['openstreetmap']
        )
        all_leads.extend(leads)
    
    gen.leads = all_leads
    gen.deduplicate_leads()
    gen.print_summary()
    gen.export_to_csv("boston_restaurants.csv")


def example_error_handling():
    """Demonstrate graceful error handling"""
    print("=" * 60)
    print("EXAMPLE 10: Error Handling")
    print("=" * 60)
    
    gen = LeadGenerator()
    
    # Try multiple APIs, some might fail if keys not set
    apis = ['serpapi', 'zenserp', 'dataforseo', 'openstreetmap', 'foursquare']
    
    print("Attempting to use all APIs...")
    print("(Some may show warnings if API keys are not configured)\n")
    
    leads = gen.generate_leads(
        keywords=["coffee shop"],
        location="Denver, CO",
        use_apis=apis
    )
    
    print(f"\n✓ Successfully collected {len(leads)} leads")
    print("The script continues even if some APIs fail!")


def interactive_menu():
    """Interactive menu to choose examples"""
    examples = {
        '1': ('Basic Search (OpenStreetMap only)', example_basic_search),
        '2': ('Multi-Keyword Search', example_multi_keyword),
        '3': ('Location Comparison', example_location_comparison),
        '4': ('API Comparison', example_api_comparison),
        '5': ('Foursquare Specific', example_foursquare_specific),
        '6': ('SerpAPI Local Business', example_serpapi_local),
        '7': ('Industry Specific (Healthcare)', example_industry_specific),
        '8': ('Export Formats Demo', example_export_formats),
        '9': ('Batch Processing', example_batch_processing),
        '10': ('Error Handling Demo', example_error_handling),
    }
    
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║       LEAD GENERATION - USAGE EXAMPLES                    ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    print("Choose an example to run:\n")
    for key, (description, _) in examples.items():
        print(f"  {key}. {description}")
    
    print("\n  0. Run all examples")
    print("  q. Quit\n")
    
    choice = input("Enter your choice: ").strip()
    
    if choice == 'q':
        print("Goodbye!")
        return
    elif choice == '0':
        print("\nRunning all examples...\n")
        for _, (description, func) in examples.items():
            print(f"\n{'='*60}")
            print(f"Running: {description}")
            print(f"{'='*60}")
            try:
                func()
            except Exception as e:
                print(f"❌ Error: {e}")
            print("\n")
    elif choice in examples:
        description, func = examples[choice]
        print(f"\nRunning: {description}\n")
        try:
            func()
        except Exception as e:
            print(f"❌ Error: {e}")
    else:
        print("Invalid choice!")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Run specific example from command line
        example_num = sys.argv[1]
        examples_map = {
            '1': example_basic_search,
            '2': example_multi_keyword,
            '3': example_location_comparison,
            '4': example_api_comparison,
            '5': example_foursquare_specific,
            '6': example_serpapi_local,
            '7': example_industry_specific,
            '8': example_export_formats,
            '9': example_batch_processing,
            '10': example_error_handling,
        }
        
        if example_num in examples_map:
            examples_map[example_num]()
        else:
            print(f"Unknown example: {example_num}")
            print("Usage: python examples.py [1-10]")
    else:
        # Interactive mode
        interactive_menu()
