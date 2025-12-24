"""
Configuration management for Lead Engine.
"""
from pathlib import Path
from dotenv import load_dotenv
import os
from dataclasses import dataclass, field
from typing import Optional, List
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
if not GOOGLE_MAPS_API_KEY:
    raise RuntimeError("GOOGLE_MAPS_API_KEY not set")




@dataclass
class Config:
    """Configuration for the Lead Engine."""
    
    # Google API
    google_api_key: str = field(default_factory=lambda: os.environ.get("GOOGLE_MAPS_API_KEY", ""))
    
    # Search parameters
    query: str = ""
    location: str = ""
    queries_csv: Optional[str] = None
    
    # Rate limiting
    max_results: int = 100
    max_pages: int = 3  # Google returns max 20 results per page, 60 max total
    sleep_ms: int = 200
    queries_per_second: int = 10
    
    # Crawler settings
    crawl_enabled: bool = True
    max_pages_per_domain: int = 6
    crawl_timeout: int = 10
    crawl_retries: int = 2
    user_agent: str = "LeadEngine/1.0 (compatible; business research)"
    
    # Cache settings
    cache_db: str = "lead_cache.db"
    use_cache: bool = True
    
    # Output settings
    output_dir: str = "output"
    output_prefix: str = "leads"
    
    # Logging
    log_level: str = "INFO"
    log_json: bool = False
    
    # Resume capability
    resume: bool = False
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.google_api_key:
            # Try loading from .env file
            env_file = Path(".env")
            if env_file.exists():
                with open(env_file) as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("GOOGLE_MAPS_API_KEY="):
                            self.google_api_key = line.split("=", 1)[1].strip().strip('"\'')
                            break
        
        # Create output directory
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors."""
        errors = []
        
        if not self.google_api_key:
            errors.append("GOOGLE_MAPS_API_KEY not set")
        
        if not self.query and not self.queries_csv:
            errors.append("Either --query or --queries-csv must be provided")
        
        if self.query and not self.location:
            errors.append("--location required when using --query")
        
        if self.max_results < 1:
            errors.append("--max-results must be positive")
        
        if self.max_pages < 1 or self.max_pages > 3:
            errors.append("--max-pages must be between 1 and 3")
        
        return errors
    
    @classmethod
    def from_args(cls, args) -> "Config":
        """Create Config from argparse namespace."""
        return cls(
            google_api_key=args.api_key or os.environ.get("GOOGLE_MAPS_API_KEY", ""),
            query=args.query or "",
            location=args.location or "",
            queries_csv=args.queries_csv,
            max_results=args.max_results,
            max_pages=args.max_pages,
            sleep_ms=args.sleep_ms,
            queries_per_second=args.qps,
            crawl_enabled=not args.no_crawl,
            max_pages_per_domain=args.max_crawl_pages,
            crawl_timeout=args.crawl_timeout,
            cache_db=args.cache_db,
            use_cache=not args.no_cache,
            output_dir=args.output_dir,
            output_prefix=args.output_prefix,
            log_level=args.log_level,
            log_json=args.log_json,
            resume=args.resume,
        )

