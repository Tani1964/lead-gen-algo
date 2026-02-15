# Quick Start Guide

Get your lead generation script running in 5 minutes!

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Set Up API Keys (Optional)

You can start with OpenStreetMap which requires no API key!

### Option A: Environment Variables (Recommended)

```bash
export SERPAPI_KEY="your_key_here"
export FOURSQUARE_API_KEY="your_key_here"
```

### Option B: Create .env file

```bash
cp .env.example .env
# Edit .env and add your API keys
```

## Step 3: Test with Free APIs

Run the script with just OpenStreetMap (no API key needed):

```bash
python lead-gen-script.py
```

The default script will search for:
- plumbers near me
- digital marketing agency
- real estate agents
- restaurants
- coffee shops

In location: **New York, NY**

## Step 4: Customize Your Search

Edit [lead-gen-script.py](lead-gen-script.py) and modify the `main()` function:

```python
# Change keywords
keywords = [
    "your business type here",
    "another keyword"
]

# Change location
location = "Your City, State"

# Choose APIs to use
apis_to_use = ['openstreetmap', 'foursquare']  # Start with free ones
```

## Step 5: View Results

After running, you'll get:
- `leads_TIMESTAMP.json` - Full lead data
- `leads_TIMESTAMP.csv` - Spreadsheet format
- Console summary of results

## Quick Examples

### Example 1: Find Local Restaurants (Free)

```python
from lead_gen_script import LeadGenerator

gen = LeadGenerator()
leads = gen.search_openstreetmap("restaurants", "San Francisco, CA")
gen.leads = leads
gen.export_to_csv("restaurants.csv")
```

### Example 2: Find Service Businesses

```python
keywords = ["plumbers", "electricians", "contractors"]
location = "Chicago, IL"
apis = ['openstreetmap']  # Free!

gen = LeadGenerator()
leads = gen.generate_leads(keywords, location, apis)
gen.deduplicate_leads()
gen.print_summary()
gen.export_to_csv("service_businesses.csv")
```

### Example 3: Using Foursquare (Requires Free API Key)

Sign up at https://developer.foursquare.com/

```bash
export FOURSQUARE_API_KEY="your_key"
```

```python
gen = LeadGenerator()
leads = gen.search_foursquare("coffee shops", "Seattle, WA", limit=50)
gen.leads = leads
gen.export_to_json("coffee_shops.json")
```

## Where to Get API Keys (Free Tiers)

| API | Sign Up Link | Free Tier |
|-----|-------------|-----------|
| SerpAPI | https://serpapi.com/users/sign_up | 100 searches/month |
| Zenserp | https://app.zenserp.com/register | 50 searches/month |
| Foursquare | https://foursquare.com/developers/signup | 950 calls/day |
| ScraperAPI | https://www.scraperapi.com/signup | 1,000 requests/month |
| DataForSEO | https://app.dataforseo.com/register | $1 free trial credit |

**OpenStreetMap** requires no API key! ✨

## Troubleshooting

### No results?
- Make sure your keywords are specific
- Try a different location
- Check if API keys are set correctly

### "API key not configured" warning?
```bash
# Check your environment variable
echo $SERPAPI_KEY

# Or use .env file instead
```

### Rate limit errors?
- Add more delay: edit `time.sleep(1)` to `time.sleep(2)` in the script
- Use fewer APIs at once
- Spread searches over time

## Next Steps

1. ✅ Test with OpenStreetMap (no setup required)
2. 📝 Customize keywords for your industry
3. 🔑 Add API keys for more data sources
4. 📊 Analyze your exported CSV/JSON files
5. 🚀 Automate with cron jobs or schedulers

## Need Help?

- Check the full [README.md](README.md) for detailed documentation
- Review [config_example.py](config_example.py) for industry-specific templates
- Read API documentation for troubleshooting

---

**Pro Tip**: Start with just 1-2 keywords and one location to test. Once you see results, scale up!
