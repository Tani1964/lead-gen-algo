# Lead Generation Script

A comprehensive Python script for generating business leads using multiple APIs and keyword-based searches.

## Features

- **Multi-API Integration**: Searches across 6 different data sources
- **Keyword-Based Search**: Generate leads using custom keywords
- **Location Targeting**: Search in specific geographic locations
- **Deduplication**: Automatically removes duplicate leads
- **Multiple Export Formats**: Save results as JSON or CSV
- **Rate Limiting**: Built-in delays to respect API limits
- **Error Handling**: Graceful handling of API failures

## APIs Supported

1. **SerpAPI** - Google search results and local businesses
2. **Zenserp** - Alternative search API with organic results
3. **DataForSEO** - SEO data and search engine results
4. **ScraperAPI** - Web scraping for contact information
5. **OpenStreetMap** - Free geographic data and places
6. **Foursquare API** - Places and business information

## Installation

### Prerequisites

- Python 3.7 or higher
- pip package manager

### Install Dependencies

```bash
pip install requests
```

## Configuration

### API Keys Setup

Create environment variables for your API keys:

```bash
# SerpAPI (https://serpapi.com/)
export SERPAPI_KEY="your_serpapi_key"

# Zenserp (https://zenserp.com/)
export ZENSERP_KEY="your_zenserp_key"

# DataForSEO (https://dataforseo.com/)
export DATAFORSEO_LOGIN="your_email"
export DATAFORSEO_PASSWORD="your_password"

# ScraperAPI (https://scraperapi.com/)
export SCRAPERAPI_KEY="your_scraperapi_key"

# Foursquare (https://developer.foursquare.com/)
export FOURSQUARE_API_KEY="your_fsq_api_key"
```

**Note**: OpenStreetMap doesn't require an API key but has rate limits. Please use responsibly.

### Alternative: Use a .env file

Create a `.env` file in the project directory:

```env
SERPAPI_KEY=your_serpapi_key
ZENSERP_KEY=your_zenserp_key
DATAFORSEO_LOGIN=your_email
DATAFORSEO_PASSWORD=your_password
SCRAPERAPI_KEY=your_scraperapi_key
FOURSQUARE_API_KEY=your_fsq_api_key
```

Then load it in your script:

```python
from dotenv import load_dotenv
load_dotenv()
```

Install python-dotenv:

```bash
pip install python-dotenv
```

## Usage

### Basic Usage

Run the script with default settings:

```bash
python lead-gen-script.py
```

### Custom Keywords

Edit the `main()` function in the script to use your own keywords:

```python
keywords = [
    "your keyword 1",
    "your keyword 2",
    "your keyword 3"
]
```

### Programmatic Usage

```python
from lead_gen_script import LeadGenerator

# Initialize
generator = LeadGenerator()

# Define keywords and location
keywords = ["coffee shops", "restaurants"]
location = "San Francisco, CA"

# Choose which APIs to use
apis = ['serpapi', 'foursquare', 'openstreetmap']

# Generate leads
leads = generator.generate_leads(
    keywords=keywords,
    location=location,
    use_apis=apis
)

# Remove duplicates
generator.deduplicate_leads()

# Export
generator.export_to_json("my_leads.json")
generator.export_to_csv("my_leads.csv")
```

### API-Specific Searches

```python
generator = LeadGenerator()

# Use only Foursquare
leads = generator.search_foursquare("coffee shops", "Boston, MA")

# Use only OpenStreetMap
leads = generator.search_openstreetmap("restaurants", "Chicago, IL")

# Use only SerpAPI
leads = generator.search_serpapi("plumbers near me", "Austin, TX")
```

## Output Format

### JSON Output

```json
[
  {
    "source": "foursquare",
    "name": "Blue Bottle Coffee",
    "fsq_id": "49d4a8f9f964a520315b1fe3",
    "categories": ["Coffee Shop", "Café"],
    "location": {
      "address": "300 Massachusetts Ave",
      "locality": "Cambridge",
      "region": "MA"
    },
    "keyword": "coffee shops",
    "timestamp": "2026-02-15T10:30:00"
  }
]
```

### CSV Output

Flattened structure with all fields as columns. Nested objects are converted to JSON strings.

## API Rate Limits & Costs

| API           | Free Tier            | Rate Limit      | Notes                |
| ------------- | -------------------- | --------------- | -------------------- |
| SerpAPI       | 100 searches/month   | No strict limit | Paid plans available |
| Zenserp       | 50 searches/month    | No strict limit | Paid plans available |
| DataForSEO    | 100 searches/month   | No strict limit | Credit-based system  |
| ScraperAPI    | 1,000 requests/month | 5 req/sec       | Paid plans available |
| OpenStreetMap | Free                 | 1 req/sec       | Must use User-Agent  |
| Foursquare    | Free tier available  | 950 calls/day   | Places API           |

**Important**: Always check the latest pricing and limits on each provider's website.

## Best Practices

1. **Start with Free APIs**: Test with OpenStreetMap and free tiers first
2. **Use Specific Keywords**: More specific keywords yield better results
3. **Respect Rate Limits**: The script includes delays, but monitor usage
4. **Deduplicate Results**: Always run `deduplicate_leads()` before exporting
5. **Test Small Batches**: Start with 1-2 keywords to test API configuration
6. **Monitor API Quotas**: Keep track of your usage across different APIs

## Troubleshooting

### "API key not configured" warnings

Make sure you've set the environment variables correctly:

```bash
echo $SERPAPI_KEY  # Should print your key
```

### No results returned

- Check your API key is valid
- Verify you have remaining quota
- Try different keywords or locations
- Check API status pages

### Rate limit errors

- Increase the `time.sleep()` values in the script
- Reduce the number of simultaneous API calls
- Use fewer keywords per run

## Example Lead Generation Workflows

### Real Estate Agents

```python
keywords = [
    "real estate agents",
    "property management",
    "real estate broker"
]
location = "Miami, FL"
apis = ['serpapi', 'foursquare']
```

### Local Services

```python
keywords = [
    "plumbers",
    "electricians",
    "HVAC contractors",
    "landscapers"
]
location = "Phoenix, AZ"
apis = ['openstreetmap', 'serpapi', 'foursquare']
```

### Restaurants & Hospitality

```python
keywords = [
    "restaurants",
    "cafes",
    "bars",
    "hotels"
]
location = "Seattle, WA"
apis = ['foursquare', 'openstreetmap']
```

## Extending the Script

### Adding Contact Extraction

Use ScraperAPI to extract email and phone numbers from websites:

```python
def extract_contacts(url):
    import re
    from bs4 import BeautifulSoup

    result = generator.scrape_with_scraperapi(url)
    if result:
        soup = BeautifulSoup(result['html'], 'html.parser')
        # Extract emails
        emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', soup.get_text())
        # Extract phone numbers
        phones = re.findall(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', soup.get_text())
        return {'emails': emails, 'phones': phones}
```

### Adding Database Storage

```python
import sqlite3

def save_to_database(leads):
    conn = sqlite3.connect('leads.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS leads
                 (id INTEGER PRIMARY KEY, source TEXT, title TEXT,
                  link TEXT, keyword TEXT, timestamp TEXT)''')

    for lead in leads:
        c.execute("INSERT INTO leads VALUES (NULL,?,?,?,?,?)",
                 (lead.get('source'), lead.get('title'),
                  lead.get('link'), lead.get('keyword'),
                  lead.get('timestamp')))

    conn.commit()
    conn.close()
```

## License

This script is provided as-is for educational and commercial use.

## Disclaimer

- Always comply with each API's Terms of Service
- Respect robots.txt and website scraping policies
- Use data responsibly and in accordance with privacy laws (GDPR, CCPA, etc.)
- Rate limiting is implemented but monitor your usage
- This script is for lead generation; verify all data before use

## Support

For issues or questions:

1. Check API documentation for each service
2. Verify your API keys and quotas
3. Review error messages in the console output
4. Test with a single API first to isolate issues

## Version History

- **v1.0** (2026-02-15)
  - Initial release
  - Support for 6 APIs
  - JSON and CSV export
  - Deduplication functionality
  - Rate limiting and error handling
