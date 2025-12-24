"""
Lead Engine - Production-ready lead generation from Google Places API.

Generate business leads from keyword + location searches, then enrich
with emails by crawling business websites.
"""

__version__ = "1.0.0"

from lead_engine.config import Config
from lead_engine.cache import LeadCache
from lead_engine.places import PlacesAcquisition
from lead_engine.crawler import WebsiteCrawler
from lead_engine.extractor import EmailExtractor, PhoneNormalizer
from lead_engine.dedupe import LeadDeduplicator
from lead_engine.output import OutputWriter

__all__ = [
    "Config",
    "LeadCache",
    "PlacesAcquisition",
    "WebsiteCrawler",
    "EmailExtractor",
    "PhoneNormalizer",
    "LeadDeduplicator",
    "OutputWriter",
]

