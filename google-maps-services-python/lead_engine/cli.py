"""
Command-line interface for Lead Engine.
"""

import argparse
import sys
import os


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser for CLI."""
    
    parser = argparse.ArgumentParser(
        prog='lead_engine',
        description='Generate business leads from Google Places API with email enrichment.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Single query
  python -m lead_engine --query "plumbers" --location "Austin, TX" --max-results 100

  # From CSV file
  python -m lead_engine --queries-csv queries.csv --max-results 200

  # Resume previous run
  python -m lead_engine --query "electricians" --location "Dallas, TX" --resume

  # Without website crawling
  python -m lead_engine --query "roofing" --location "Houston, TX" --no-crawl

Environment:
  GOOGLE_MAPS_API_KEY    Your Google Maps API key (or use --api-key)
'''
    )
    
    # Input options
    input_group = parser.add_argument_group('Input Options')
    input_group.add_argument(
        '--query', '-q',
        type=str,
        help='Search query (e.g., "plumbers", "roofing contractors")'
    )
    input_group.add_argument(
        '--location', '-l',
        type=str,
        help='Location for search (e.g., "Austin, TX", "Brooklyn, NY")'
    )
    input_group.add_argument(
        '--queries-csv',
        type=str,
        help='CSV file with query,location columns'
    )
    
    # API options
    api_group = parser.add_argument_group('API Options')
    api_group.add_argument(
        '--api-key',
        type=str,
        default=os.environ.get('GOOGLE_MAPS_API_KEY', ''),
        help='Google Maps API key (default: GOOGLE_MAPS_API_KEY env var)'
    )
    api_group.add_argument(
        '--max-results',
        type=int,
        default=100,
        help='Maximum results to fetch per query (default: 100)'
    )
    api_group.add_argument(
        '--max-pages',
        type=int,
        default=3,
        choices=[1, 2, 3],
        help='Maximum search result pages (1-3, default: 3)'
    )
    api_group.add_argument(
        '--sleep-ms',
        type=int,
        default=200,
        help='Sleep between API calls in ms (default: 200)'
    )
    api_group.add_argument(
        '--qps',
        type=int,
        default=10,
        help='Queries per second limit (default: 10)'
    )
    
    # Crawler options
    crawl_group = parser.add_argument_group('Crawler Options')
    crawl_group.add_argument(
        '--no-crawl',
        action='store_true',
        help='Disable website crawling for emails'
    )
    crawl_group.add_argument(
        '--max-crawl-pages',
        type=int,
        default=6,
        help='Max pages to crawl per domain (default: 6)'
    )
    crawl_group.add_argument(
        '--crawl-timeout',
        type=int,
        default=10,
        help='Crawl request timeout in seconds (default: 10)'
    )
    
    # Cache options
    cache_group = parser.add_argument_group('Cache Options')
    cache_group.add_argument(
        '--no-cache',
        action='store_true',
        help='Disable caching (not recommended)'
    )
    cache_group.add_argument(
        '--cache-db',
        type=str,
        default='lead_cache.db',
        help='Cache database path (default: lead_cache.db)'
    )
    cache_group.add_argument(
        '--resume',
        action='store_true',
        help='Resume from previous progress'
    )
    
    # Output options
    output_group = parser.add_argument_group('Output Options')
    output_group.add_argument(
        '--output-dir', '-o',
        type=str,
        default='output',
        help='Output directory (default: output)'
    )
    output_group.add_argument(
        '--output-prefix',
        type=str,
        default='leads',
        help='Output file prefix (default: leads)'
    )
    
    # Logging options
    log_group = parser.add_argument_group('Logging Options')
    log_group.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Log level (default: INFO)'
    )
    log_group.add_argument(
        '--log-json',
        action='store_true',
        help='Output logs in JSON format'
    )
    log_group.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress progress output'
    )
    
    return parser


def parse_args(args=None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = create_parser()
    return parser.parse_args(args)


def validate_args(args: argparse.Namespace) -> list:
    """
    Validate parsed arguments.
    
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    
    # Check API key
    if not args.api_key:
        errors.append("GOOGLE_MAPS_API_KEY not set. Use --api-key or set environment variable.")
    
    # Check input source
    if not args.query and not args.queries_csv:
        errors.append("Must provide either --query or --queries-csv")
    
    if args.query and not args.location:
        errors.append("--location is required when using --query")
    
    if args.queries_csv and not os.path.exists(args.queries_csv):
        errors.append(f"Queries CSV file not found: {args.queries_csv}")
    
    # Validate numeric ranges
    if args.max_results < 1:
        errors.append("--max-results must be at least 1")
    
    if args.sleep_ms < 0:
        errors.append("--sleep-ms cannot be negative")
    
    if args.qps < 1:
        errors.append("--qps must be at least 1")
    
    return errors

