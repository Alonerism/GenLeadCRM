# Lead Engine

**Production-ready lead generation from Google Places API with email enrichment.**

Generate hundreds/thousands of business leads from keyword + location searches, then enrich by crawling business websites to extract emails. Output is a clean CSV and JSONL.

## Features

- 🔍 **Google Places Search** - Text search with pagination and field optimization
- 📧 **Email Extraction** - Crawl business websites to find contact emails
- 🎯 **Quality Flags** - Classify emails as personal vs generic (no AI required)
- 💾 **SQLite Caching** - Aggressive caching to minimize API costs and enable resume
- 🔄 **Deduplication** - By place_id, phone number, and website domain
- 📊 **Multiple Outputs** - CSV for spreadsheets, JSONL for data pipelines
- ⚡ **Rate Limiting** - Built-in QPS controls to avoid API bans
- 🔁 **Resume Support** - Continue interrupted runs from where you left off

## Quick Start

### 1. Setup

```bash
# Clone the repo
git clone https://github.com/yourusername/lead-engine.git
cd lead-engine

# Install dependencies
pip install -r requirements.txt

# Set your API key
cp .env.example .env
# Edit .env and add your GOOGLE_MAPS_API_KEY
```

### 2. Get Your API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create a new project or select existing
3. Enable **Places API** 
4. Create an API key
5. Add it to your `.env` file

### 3. Run

```bash
# Single query
python -m lead_engine --query "plumbers" --location "Austin, TX" --max-results 100

# From CSV file
python -m lead_engine --queries-csv scripts/sample_queries.csv --max-results 50

# Without website crawling (faster, less data)
python -m lead_engine --query "electricians" --location "Dallas, TX" --no-crawl

# Resume interrupted run
python -m lead_engine --query "roofers" --location "Houston, TX" --resume
```

## Output Schema

### CSV (`output/leads.csv`)

| Column | Description |
|--------|-------------|
| `place_id` | Google Place ID (primary key) |
| `name` | Business name |
| `address` | Full formatted address |
| `city` | City extracted from address |
| `state` | State/province |
| `postal_code` | ZIP/postal code |
| `country` | Country |
| `phone` | Local phone number |
| `international_phone` | Phone with country code |
| `website` | Business website URL |
| `emails` | Semicolon-separated email addresses |
| `types` | Semicolon-separated business types |
| `rating` | Google rating (1-5) |
| `user_ratings_total` | Number of reviews |
| `source_query` | Search query used |
| `source_location` | Location searched |
| `fetched_at` | ISO timestamp |

### JSONL (`output/leads.jsonl`)

Same fields as CSV, but with:
- `emails` as array instead of semicolon-separated
- `types` as array instead of semicolon-separated
- `email_quality` object mapping email to quality flag ("personal" or "generic")
- `domain` extracted website domain

## CLI Options

```
Input Options:
  --query, -q           Search query (e.g., "plumbers")
  --location, -l        Location (e.g., "Austin, TX")
  --queries-csv         CSV file with query,location columns

API Options:
  --api-key             Google Maps API key (or use env var)
  --max-results         Max results per query (default: 100)
  --max-pages           Max search pages 1-3 (default: 3)
  --sleep-ms            Sleep between calls in ms (default: 200)
  --qps                 Queries per second limit (default: 10)

Crawler Options:
  --no-crawl            Disable website crawling
  --max-crawl-pages     Max pages per domain (default: 6)
  --crawl-timeout       Request timeout in seconds (default: 10)

Cache Options:
  --no-cache            Disable caching
  --cache-db            Cache database path (default: lead_cache.db)
  --resume              Resume from previous progress

Output Options:
  --output-dir, -o      Output directory (default: output)
  --output-prefix       File prefix (default: leads)

Logging Options:
  --log-level           DEBUG, INFO, WARNING, ERROR (default: INFO)
  --log-json            Output logs in JSON format
  --quiet               Suppress progress output
```

## Examples

### Generate Leads for Multiple Queries

Create a CSV file `my_queries.csv`:

```csv
query,location
plumbers,Austin TX
electricians,Austin TX
hvac contractors,Dallas TX
roofing companies,Houston TX
```

Run:

```bash
python -m lead_engine --queries-csv my_queries.csv --max-results 200
```

### Optimize for Cost

```bash
# Minimal API calls: small results, no crawling
python -m lead_engine \
  --query "dentists" \
  --location "San Francisco, CA" \
  --max-results 20 \
  --max-pages 1 \
  --no-crawl
```

### Debug Mode

```bash
python -m lead_engine \
  --query "lawyers" \
  --location "New York, NY" \
  --log-level DEBUG \
  --max-results 10
```

## Caching

The engine uses SQLite to cache:

- **Place details** - Avoids re-fetching the same business
- **Crawl results** - Avoids re-crawling the same website
- **Search progress** - Enables resume capability
- **Failures** - Track failed requests for retry

Cache is stored in `lead_cache.db` by default. Use `--cache-db` to specify a different location.

## Cost Optimization

Google Places API charges per request. This engine minimizes costs by:

1. **Field masks** - Only requesting needed fields (place_id, name, address, phone, website, types, rating)
2. **Caching** - Never re-fetching already-cached places
3. **Deduplication** - Processing each unique business only once
4. **Rate limiting** - Preventing accidental request bursts

**Estimated costs** (as of 2024):
- Text Search: $32 per 1000 requests
- Place Details: $17 per 1000 requests (Basic fields)
- ~100 leads with details ≈ $2-5

## Development

### Run Tests

```bash
# Install dev dependencies
pip install pytest responses

# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_extractor.py -v
```

### Project Structure

```
lead-engine/
├── lead_engine/           # Main application
│   ├── __init__.py
│   ├── __main__.py        # CLI entry point
│   ├── cli.py             # Argument parsing
│   ├── config.py          # Configuration
│   ├── cache.py           # SQLite caching
│   ├── places.py          # Google Places API
│   ├── crawler.py         # Website crawler
│   ├── extractor.py       # Email/phone extraction
│   ├── dedupe.py          # Deduplication
│   ├── output.py          # CSV/JSONL writers
│   └── logging_config.py  # Logging setup
├── googlemaps/            # Google Maps client library
├── tests/                 # Unit tests
│   ├── fixtures/          # Test data
│   ├── test_extractor.py
│   ├── test_dedupe.py
│   └── test_cache.py
├── scripts/               # Helper scripts
│   ├── sample_queries.csv
│   └── seed_examples.sh
├── output/                # Generated leads
├── requirements.txt
├── setup.py
└── README.md
```

## FAQ

**Q: Why no AI/LLM for email extraction?**

A: Regex-based extraction is faster, cheaper, and more reliable for well-structured data like emails. The quality classification (personal vs generic) is heuristic-based and works well without AI overhead.

**Q: How do I handle rate limits?**

A: The engine has built-in rate limiting (`--qps` flag). Default is 10 queries/second which is safe for most API quotas. Use `--sleep-ms` to add additional delays.

**Q: Can I run multiple instances?**

A: Yes, but use different cache databases (`--cache-db`) and output directories (`--output-dir`) to avoid conflicts.

**Q: Why SQLite instead of Redis/PostgreSQL?**

A: SQLite requires zero setup, works everywhere, and is fast enough for this use case. The cache file is portable and can be backed up easily.

## License

Apache 2.0 - See [LICENSE](LICENSE) for details.

The `googlemaps/` directory contains the Google Maps Services Python client library, also Apache 2.0 licensed.
