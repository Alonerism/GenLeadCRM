"""
Lead Engine - Main entry point.

Usage:
    python -m lead_engine --query "plumbers" --location "Austin, TX" --max-results 100
"""

import sys
import logging
from datetime import datetime
from typing import List, Tuple

from lead_engine.cli import parse_args, validate_args
from lead_engine.config import Config
from lead_engine.cache import LeadCache
from lead_engine.places import PlacesAcquisition, parse_queries_csv
from lead_engine.crawler import WebsiteCrawler
from lead_engine.dedupe import LeadDeduplicator, Lead, merge_leads_with_emails
from lead_engine.output import OutputWriter, ProgressTracker
from lead_engine.logging_config import setup_logging
from lead_engine.extractor import extract_domain

logger = logging.getLogger(__name__)


def run_pipeline(
    queries: List[Tuple[str, str]],
    config: Config,
    cache: LeadCache,
    progress: ProgressTracker,
) -> List[Lead]:
    """
    Run the full lead generation pipeline.
    
    Args:
        queries: List of (query, location) tuples
        config: Configuration
        cache: Cache instance
        progress: Progress tracker
        
    Returns:
        List of deduplicated leads
    """
    # Initialize components
    places_api = PlacesAcquisition(config, cache)
    crawler = WebsiteCrawler(
        cache=cache,
        max_pages=config.max_pages_per_domain,
        timeout=config.crawl_timeout,
    )
    deduplicator = LeadDeduplicator()
    
    # Collect all place results
    all_place_data = []
    
    for query, location in queries:
        logger.info(f"Processing: '{query}' in '{location}'")
        
        for place in places_api.search(query, location):
            all_place_data.append({
                'place_id': place.place_id,
                'name': place.name,
                'address': place.address,
                'phone': place.phone,
                'international_phone': place.international_phone,
                'website': place.website,
                'types': place.types,
                'rating': place.rating,
                'user_ratings_total': place.user_ratings_total,
                'source_query': query,
                'source_location': location,
                'fetched_at': datetime.utcnow().isoformat(),
            })
            
            progress.update(places=1)
    
    # Update progress with API stats
    api_stats = places_api.get_stats()
    progress.api_calls = api_stats['api_calls']
    progress.cache_hits = api_stats['cache_hits']
    
    logger.info(f"Fetched {len(all_place_data)} places, deduplicating...")
    
    # Deduplicate
    leads = deduplicator.dedupe(all_place_data)
    dedupe_stats = deduplicator.get_stats()
    logger.info(f"After dedupe: {len(leads)} unique leads (removed {dedupe_stats['total_duplicates']} duplicates)")
    
    # Crawl websites for emails
    if config.crawl_enabled:
        logger.info("Crawling websites for emails...")
        
        # Get unique websites
        websites = list(set(lead.website for lead in leads if lead.website))
        logger.info(f"Crawling {len(websites)} unique websites")
        
        crawl_results = {}
        for website in websites:
            domain = extract_domain(website)
            if not domain:
                continue
            
            result = crawler.crawl(website, use_cache=config.use_cache)
            crawl_results[domain] = result
            
            progress.update(websites=1, emails=len(result.emails))
        
        # Merge emails into leads
        leads = merge_leads_with_emails(leads, crawl_results)
    
    return leads


def main():
    """Main entry point."""
    # Parse arguments
    args = parse_args()
    
    # Setup logging
    setup_logging(
        level=args.log_level,
        json_format=args.log_json,
    )
    
    # Validate arguments
    errors = validate_args(args)
    if errors:
        for error in errors:
            logger.error(error)
        sys.exit(1)
    
    # Create config
    config = Config.from_args(args)
    
    # Initialize components
    cache = LeadCache(config.cache_db)
    output = OutputWriter(config.output_dir, config.output_prefix)
    progress = ProgressTracker(quiet=args.quiet)
    
    # Build query list
    queries: List[Tuple[str, str]] = []
    
    if args.queries_csv:
        queries = parse_queries_csv(args.queries_csv)
        logger.info(f"Loaded {len(queries)} queries from {args.queries_csv}")
    else:
        queries = [(args.query, args.location)]
    
    # Print startup info
    if not args.quiet:
        print(f"\n{'='*50}")
        print(f"Lead Engine v1.0")
        print(f"{'='*50}")
        print(f"  Queries:          {len(queries)}")
        print(f"  Max results/query: {config.max_results}")
        print(f"  Crawling:         {'enabled' if config.crawl_enabled else 'disabled'}")
        print(f"  Cache:            {config.cache_db}")
        print(f"  Output:           {config.output_dir}/")
        print(f"{'='*50}\n")
    
    try:
        # Run pipeline
        leads = run_pipeline(queries, config, cache, progress)
        
        # Write output
        output.write_leads(leads)
        
        # Write failures
        failures = cache.get_failures()
        if failures:
            output.write_failures(failures)
        
        # Print summary
        progress.finish()
        
        # Print cache stats
        cache_stats = cache.get_stats()
        if not args.quiet:
            print(f"\nCache stats:")
            print(f"  Places cached:    {cache_stats['places_cached']}")
            print(f"  Domains crawled:  {cache_stats['domains_crawled']}")
            print(f"  Failures logged:  {cache_stats['failures']}")
            print(f"\nOutput files:")
            print(f"  {output.csv_path}")
            print(f"  {output.jsonl_path}")
            if failures:
                print(f"  {output.failures_path}")
        
        return 0
        
    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
        progress.finish()
        return 130
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())

