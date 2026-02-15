#!/usr/bin/env python3
"""
Example configuration file for lead generation
Customize this file with your specific keywords and settings
"""

# Lead Generation Configuration
LEAD_CONFIG = {
    # Keywords to search for
    "keywords": [
        "plumbers near me",
        "digital marketing agency",
        "real estate agents",
        "restaurants",
        "coffee shops"
    ],
    
    # Location to search in
    "location": "New York, NY",
    
    # Which APIs to use (comment out any you don't want to use)
    "apis": [
        'openstreetmap',  # Free, no API key needed
        'serpapi',        # 100 searches/month free
        'zenserp',        # 50 searches/month free
        'dataforseo',     # Paid, credit-based
        'foursquare',     # Free tier available
    ],
    
    # Export settings
    "export": {
        "format": ["json", "csv"],  # Export formats
        "deduplicate": True,         # Remove duplicates before export
    },
    
    # Rate limiting (seconds between API calls)
    "rate_limit": {
        "default": 1,      # Default delay between calls
        "openstreetmap": 1.5,  # OSM requires respectful rate limiting
    }
}


# Example: Multiple locations search
MULTI_LOCATION_CONFIG = {
    "keywords": ["coffee shops"],
    "locations": [
        "New York, NY",
        "Los Angeles, CA",
        "Chicago, IL",
        "Houston, TX",
        "Phoenix, AZ"
    ],
    "apis": ['foursquare', 'openstreetmap']
}


# Example: Industry-specific lead generation
INDUSTRY_CONFIGS = {
    "real_estate": {
        "keywords": [
            "real estate agents",
            "property management companies",
            "real estate brokers",
            "commercial real estate",
            "residential real estate"
        ],
        "location": "Miami, FL",
        "apis": ['serpapi', 'dataforseo']
    },
    
    "home_services": {
        "keywords": [
            "plumbers",
            "electricians",
            "HVAC contractors",
            "roofing companies",
            "landscapers",
            "general contractors"
        ],
        "location": "Austin, TX",
        "apis": ['serpapi', 'openstreetmap', 'foursquare']
    },
    
    "healthcare": {
        "keywords": [
            "dentists",
            "chiropractors",
            "physical therapy",
            "urgent care",
            "medical clinics"
        ],
        "location": "Seattle, WA",
        "apis": ['serpapi', 'foursquare']
    },
    
    "restaurants": {
        "keywords": [
            "restaurants",
            "cafes",
            "food trucks",
            "catering services",
            "bakeries"
        ],
        "location": "Portland, OR",
        "apis": ['foursquare', 'openstreetmap']
    },
    
    "professional_services": {
        "keywords": [
            "law firms",
            "accounting firms",
            "marketing agencies",
            "consulting firms",
            "financial advisors"
        ],
        "location": "Boston, MA",
        "apis": ['serpapi', 'dataforseo']
    }
}


# DataForSEO location codes (some common ones)
DATAFORSEO_LOCATIONS = {
    "United States": 2840,
    "New York": 1023191,
    "Los Angeles": 1023768,
    "Chicago": 1016367,
    "Houston": 1026266,
    "Phoenix": 1023936,
    "Philadelphia": 1023927,
    "San Antonio": 1022481,
    "San Diego": 1023926,
    "Dallas": 1019930,
    "United Kingdom": 2826,
    "Canada": 2124,
}


# Foursquare categories (some examples)
FOURSQUARE_CATEGORIES = {
    "restaurants": "13065",
    "coffee": "13032",
    "bars": "13003",
    "retail": "17000",
    "professional_services": "12000",
    "health": "15000",
    "automotive": "19000",
}
