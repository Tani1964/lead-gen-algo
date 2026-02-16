#!/usr/bin/env python3
"""
Test script to verify API configurations and connectivity
Run this before using the main lead generation script
"""

import os
import sys

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("📄 Loading .env file...")
except ImportError:
    print("⚠️  python-dotenv not installed, using system environment variables only")


def check_python_version():
    """Check if Python version is adequate"""
    print("Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 7:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro} (OK)")
        return True
    else:
        print(f"✗ Python {version.major}.{version.minor} (Need 3.7+)")
        return False


def check_dependencies():
    """Check if required packages are installed"""
    print("\nChecking dependencies...")
    
    required = ['requests']
    optional = ['dotenv']
    
    all_good = True
    
    for package in required:
        try:
            __import__(package)
            print(f"✓ {package} installed")
        except ImportError:
            print(f"✗ {package} NOT installed (REQUIRED)")
            print(f"  Install with: pip install {package}")
            all_good = False
    
    for package in optional:
        try:
            __import__(package)
            print(f"✓ {package} installed (optional)")
        except ImportError:
            print(f"⚠ {package} NOT installed (optional)")
    
    return all_good


def check_api_keys():
    """Check which API keys are configured"""
    print("\nChecking API keys...")
    
    api_keys = {
        'SERPAPI_KEY': 'SerpAPI',
        'ZENSERP_KEY': 'Zenserp',
        'DATAFORSEO_LOGIN': 'DataForSEO Login',
        'DATAFORSEO_PASSWORD': 'DataForSEO Password',
        'SCRAPERAPI_KEY': 'ScraperAPI',
        'FOURSQUARE_API_KEY': 'Foursquare'
    }
    
    configured = []
    not_configured = []
    
    for env_var, name in api_keys.items():
        value = os.getenv(env_var)
        if value and len(value) > 0:
            print(f"✓ {name:20s} configured")
            configured.append(name)
        else:
            print(f"✗ {name:20s} NOT configured")
            not_configured.append(name)
    
    print(f"\n✓ OpenStreetMap         (No API key needed)")
    
    print(f"\nSummary: {len(configured)}/6 paid APIs configured")
    
    if not configured:
        print("\n⚠️  No API keys configured!")
        print("   You can still use OpenStreetMap (free, no key needed)")
        print("   To add API keys, see .env.example file")
    
    return len(configured) > 0 or True  # Always return True since OSM works


def test_openstreetmap():
    """Test OpenStreetMap API (no key needed)"""
    print("\nTesting OpenStreetMap API...")
    
    try:
        import requests
        
        params = {
            "q": "coffee shop Portland",
            "format": "json",
            "limit": 1
        }
        
        headers = {
            "User-Agent": "LeadGenScript/1.0 (Test)"
        }
        
        response = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params=params,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ OpenStreetMap API working! (Found {len(data)} results)")
            return True
        else:
            print(f"✗ OpenStreetMap returned status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ OpenStreetMap test failed: {str(e)}")
        return False


def test_serpapi():
    """Test SerpAPI if key is configured"""
    key = os.getenv('SERPAPI_KEY')
    if not key:
        return None
    
    print("\nTesting SerpAPI...")
    
    try:
        import requests
        
        params = {
            "q": "coffee",
            "api_key": key,
            "engine": "google",
            "num": 1
        }
        
        response = requests.get(
            "https://serpapi.com/search",
            params=params,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✓ SerpAPI working!")
            return True
        else:
            print(f"✗ SerpAPI returned status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ SerpAPI test failed: {str(e)}")
        return False


def test_foursquare():
    """Test Foursquare API if key is configured"""
    key = os.getenv('FOURSQUARE_API_KEY')
    if not key:
        return None
    
    print("\nTesting Foursquare API...")
    
    try:
        import requests
        
        headers = {
            "Authorization": key,
            "Accept": "application/json"
        }
        
        params = {
            "query": "coffee",
            "near": "New York",
            "limit": 1
        }
        
        response = requests.get(
            "https://api.foursquare.com/v3/places/search",
            headers=headers,
            params=params,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✓ Foursquare API working!")
            return True
        else:
            print(f"✗ Foursquare returned status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Foursquare test failed: {str(e)}")
        return False


def main():
    """Run all tests"""
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║         LEAD GENERATION SETUP TEST                        ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    results = []
    
    # Check Python
    results.append(("Python Version", check_python_version()))
    
    # Check dependencies
    results.append(("Dependencies", check_dependencies()))
    
    # Check API keys
    results.append(("API Keys", check_api_keys()))
    
    # Test APIs
    results.append(("OpenStreetMap", test_openstreetmap()))
    
    serp_result = test_serpapi()
    if serp_result is not None:
        results.append(("SerpAPI", serp_result))
    
    fsq_result = test_foursquare()
    if fsq_result is not None:
        results.append(("Foursquare", fsq_result))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result is True)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name:20s} {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if all(result for _, result in results):
        print("\n🎉 All tests passed! You're ready to generate leads!")
    elif any(name == "OpenStreetMap" and result for name, result in results):
        print("\n✓ You can start with OpenStreetMap (no API key needed)")
        print("  Add more API keys later to get more data sources")
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")
        print("   You can still try running the script - it will skip failed APIs")
    
    print("\nNext steps:")
    print("  1. Run: python lead-gen-script.py")
    print("  2. Or try: python examples.py")
    print("  3. Read: QUICKSTART.md for more info")


if __name__ == "__main__":
    main()
