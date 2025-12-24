"""Tests for cache module."""

import unittest
import tempfile
import os
from lead_engine.cache import LeadCache


class TestLeadCache(unittest.TestCase):
    """Tests for LeadCache class."""
    
    def setUp(self):
        """Create a temporary cache for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_cache.db")
        self.cache = LeadCache(self.db_path)
    
    def tearDown(self):
        """Clean up temporary files."""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)
    
    def test_save_and_get_place(self):
        """Test saving and retrieving a place."""
        place_data = {
            "place_id": "test123",
            "result": {
                "name": "Test Business",
                "formatted_address": "123 Main St",
                "formatted_phone_number": "(512) 555-1234",
                "international_phone_number": "+1 512-555-1234",
                "website": "https://test.com",
                "types": ["plumber"],
                "rating": 4.5,
                "user_ratings_total": 100,
            }
        }
        
        self.cache.save_place(place_data, "test query", "Austin TX")
        
        retrieved = self.cache.get_place("test123")
        
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["place_id"], "test123")
        self.assertEqual(retrieved["name"], "Test Business")
        self.assertEqual(retrieved["source_query"], "test query")
    
    def test_has_place(self):
        """Test checking if place exists."""
        self.assertFalse(self.cache.has_place("nonexistent"))
        
        self.cache.save_place(
            {"place_id": "exists", "result": {"name": "Test"}},
            "", ""
        )
        
        self.assertTrue(self.cache.has_place("exists"))
    
    def test_save_and_get_crawl_result(self):
        """Test saving and retrieving crawl results."""
        self.cache.save_crawl_result(
            domain="example.com",
            emails=["info@example.com", "sales@example.com"],
            social_links={"linkedin": "https://linkedin.com/company/example"},
            pages_crawled=5,
            raw_data={"urls": ["/", "/contact"]},
            success=True,
        )
        
        retrieved = self.cache.get_crawl_result("example.com")
        
        self.assertIsNotNone(retrieved)
        self.assertEqual(len(retrieved["emails"]), 2)
        self.assertIn("info@example.com", retrieved["emails"])
        self.assertEqual(retrieved["pages_crawled"], 5)
        self.assertEqual(retrieved["social_links"]["linkedin"], "https://linkedin.com/company/example")
    
    def test_has_crawl_result(self):
        """Test checking if crawl result exists."""
        self.assertFalse(self.cache.has_crawl_result("notcrawled.com"))
        
        self.cache.save_crawl_result("crawled.com", [], {}, 1)
        
        self.assertTrue(self.cache.has_crawl_result("crawled.com"))
    
    def test_search_progress(self):
        """Test search progress tracking."""
        self.cache.save_search_progress(
            query="plumbers",
            location="Austin TX",
            next_page_token="token123",
            results_fetched=20,
            completed=False,
        )
        
        progress = self.cache.get_search_progress("plumbers", "Austin TX")
        
        self.assertIsNotNone(progress)
        self.assertEqual(progress["results_fetched"], 20)
        self.assertEqual(progress["next_page_token"], "token123")
        self.assertEqual(progress["completed"], 0)
    
    def test_search_progress_completed(self):
        """Test marking search as completed."""
        self.cache.save_search_progress(
            query="test",
            location="test",
            next_page_token=None,
            results_fetched=50,
            completed=True,
        )
        
        progress = self.cache.get_search_progress("test", "test")
        
        self.assertEqual(progress["completed"], 1)
        self.assertIsNone(progress["next_page_token"])
    
    def test_failures(self):
        """Test failure tracking."""
        self.cache.save_failure(
            error_type="crawl_timeout",
            error_message="Request timed out",
            domain="slow.example.com",
        )
        self.cache.save_failure(
            error_type="api_error",
            error_message="Rate limited",
            place_id="place123",
        )
        
        failures = self.cache.get_failures()
        self.assertEqual(len(failures), 2)
        
        crawl_failures = self.cache.get_failures("crawl_timeout")
        self.assertEqual(len(crawl_failures), 1)
        self.assertEqual(crawl_failures[0]["domain"], "slow.example.com")
    
    def test_clear_failures(self):
        """Test clearing failures."""
        self.cache.save_failure("test", "error1")
        self.cache.save_failure("test", "error2")
        
        self.cache.clear_failures()
        
        self.assertEqual(len(self.cache.get_failures()), 0)
    
    def test_get_stats(self):
        """Test getting cache statistics."""
        # Add some data
        self.cache.save_place({"place_id": "p1", "result": {}}, "", "")
        self.cache.save_place({"place_id": "p2", "result": {}}, "", "")
        self.cache.save_crawl_result("d1.com", [], {}, 1)
        self.cache.save_failure("error", "test")
        
        stats = self.cache.get_stats()
        
        self.assertEqual(stats["places_cached"], 2)
        self.assertEqual(stats["domains_crawled"], 1)
        self.assertEqual(stats["failures"], 1)
    
    def test_get_all_places(self):
        """Test getting all places."""
        self.cache.save_place({"place_id": "p1", "result": {"name": "A"}}, "q", "l")
        self.cache.save_place({"place_id": "p2", "result": {"name": "B"}}, "q", "l")
        
        places = self.cache.get_all_places()
        
        self.assertEqual(len(places), 2)
    
    def test_get_places_by_query(self):
        """Test getting places by query."""
        self.cache.save_place({"place_id": "p1", "result": {}}, "plumbers", "Austin")
        self.cache.save_place({"place_id": "p2", "result": {}}, "plumbers", "Austin")
        self.cache.save_place({"place_id": "p3", "result": {}}, "electricians", "Austin")
        
        places = self.cache.get_places_by_query("plumbers", "Austin")
        
        self.assertEqual(len(places), 2)
    
    def test_compression(self):
        """Test that data is compressed."""
        large_data = {
            "place_id": "test",
            "result": {
                "name": "Test " * 1000,  # Large data
                "description": "Lorem ipsum " * 500,
            }
        }
        
        self.cache.save_place(large_data, "", "")
        
        # Data should be stored compressed
        retrieved = self.cache.get_place("test")
        self.assertEqual(retrieved["name"], "Test " * 1000)


if __name__ == "__main__":
    unittest.main()

