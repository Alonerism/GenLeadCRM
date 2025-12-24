#!/bin/bash
# Lead Engine - Example seed script
# Runs sample queries to populate the cache and generate example output

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "========================================"
echo "Lead Engine - Seed Examples"
echo "========================================"

# Check for API key
if [ -z "$GOOGLE_MAPS_API_KEY" ]; then
    if [ -f .env ]; then
        export $(grep -v '^#' .env | xargs)
    fi
fi

if [ -z "$GOOGLE_MAPS_API_KEY" ]; then
    echo "Error: GOOGLE_MAPS_API_KEY not set"
    echo "Please set the environment variable or create a .env file"
    exit 1
fi

echo "Running with small sample (5 results per query)..."
echo ""

# Run with sample queries CSV
python -m lead_engine \
    --queries-csv scripts/sample_queries.csv \
    --max-results 5 \
    --max-pages 1 \
    --output-prefix sample_leads \
    --log-level INFO

echo ""
echo "========================================"
echo "Sample run complete!"
echo "Output files:"
echo "  - output/sample_leads.csv"
echo "  - output/sample_leads.jsonl"
echo "========================================"

