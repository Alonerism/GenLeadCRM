"""Tests for lead deduplication logic."""

import unittest
from lead_engine.dedupe import Lead, LeadDeduplicator


class TestLead(unittest.TestCase):
    """Tests for Lead dataclass."""
    
    def test_create_lead(self):
        """Test creating a lead."""
        lead = Lead(
            place_id="test123",
            name="Test Business",
            address="123 Main St, Austin, TX 78701, USA",
        )
        self.assertEqual(lead.place_id, "test123")
        self.assertEqual(lead.name, "Test Business")
        self.assertIsNotNone(lead.emails)
        self.assertIsNotNone(lead.types)
    
    def test_parse_us_address(self):
        """Test parsing US address."""
        lead = Lead(
            place_id="test",
            name="Test",
            address="123 Main St, Austin, TX 78701, USA",
        )
        self.assertEqual(lead.city, "Austin")
        self.assertEqual(lead.state, "TX")
        self.assertEqual(lead.postal_code, "78701")
        self.assertEqual(lead.country, "USA")
    
    def test_extract_domain(self):
        """Test domain extraction from website."""
        lead = Lead(
            place_id="test",
            name="Test",
            address="",
            website="https://www.example.com/about",
        )
        self.assertEqual(lead.domain, "example.com")
    
    def test_to_dict(self):
        """Test converting to dictionary."""
        lead = Lead(
            place_id="test123",
            name="Test Business",
            address="123 Main St",
            emails=["info@test.com", "sales@test.com"],
            types=["plumber", "contractor"],
        )
        d = lead.to_dict()
        self.assertEqual(d["place_id"], "test123")
        self.assertEqual(d["emails"], "info@test.com;sales@test.com")
        self.assertEqual(d["types"], "plumber;contractor")
    
    def test_to_full_dict(self):
        """Test converting to full dictionary (for JSONL)."""
        lead = Lead(
            place_id="test123",
            name="Test",
            address="",
            emails=["info@test.com"],
            types=["plumber"],
        )
        d = lead.to_full_dict()
        # Lists should remain as lists
        self.assertIsInstance(d["emails"], list)
        self.assertIsInstance(d["types"], list)


class TestLeadDeduplicator(unittest.TestCase):
    """Tests for LeadDeduplicator class."""
    
    def setUp(self):
        self.deduper = LeadDeduplicator()
    
    def test_dedupe_by_place_id(self):
        """Test deduplication by place_id."""
        leads_data = [
            {"place_id": "A", "name": "Business A", "address": "123 Main"},
            {"place_id": "B", "name": "Business B", "address": "456 Oak"},
            {"place_id": "A", "name": "Business A Copy", "address": "123 Main"},  # Duplicate
        ]
        
        leads = self.deduper.dedupe(leads_data)
        
        self.assertEqual(len(leads), 2)
        place_ids = {lead.place_id for lead in leads}
        self.assertEqual(place_ids, {"A", "B"})
    
    def test_dedupe_by_phone(self):
        """Test deduplication by phone number."""
        leads_data = [
            {"place_id": "A", "name": "Business A", "phone": "(512) 555-1234", "address": ""},
            {"place_id": "B", "name": "Business B", "phone": "512-555-1234", "address": ""},  # Same phone, different format
            {"place_id": "C", "name": "Business C", "phone": "(512) 555-5678", "address": ""},
        ]
        
        leads = self.deduper.dedupe(leads_data)
        
        self.assertEqual(len(leads), 2)
    
    def test_dedupe_by_domain(self):
        """Test deduplication by website domain."""
        leads_data = [
            {"place_id": "A", "name": "Business A", "website": "https://example.com", "address": ""},
            {"place_id": "B", "name": "Business B", "website": "https://www.example.com/about", "address": ""},  # Same domain
            {"place_id": "C", "name": "Business C", "website": "https://other.com", "address": ""},
        ]
        
        leads = self.deduper.dedupe(leads_data)
        
        self.assertEqual(len(leads), 2)
    
    def test_get_stats(self):
        """Test getting deduplication statistics."""
        leads_data = [
            {"place_id": "A", "name": "Business A", "address": ""},
            {"place_id": "A", "name": "Duplicate A", "address": ""},
            {"place_id": "B", "name": "Business B", "phone": "5555551234", "address": ""},
            {"place_id": "C", "name": "Duplicate B", "phone": "555-555-1234", "address": ""},
        ]
        
        self.deduper.dedupe(leads_data)
        stats = self.deduper.get_stats()
        
        self.assertEqual(stats["total_input"], 4)
        self.assertEqual(stats["unique_leads"], 2)
        self.assertEqual(stats["duplicates_place_id"], 1)
        self.assertEqual(stats["duplicates_phone"], 1)
    
    def test_reset(self):
        """Test resetting deduplicator state."""
        leads_data = [
            {"place_id": "A", "name": "Business", "address": ""},
        ]
        
        self.deduper.dedupe(leads_data)
        self.deduper.reset()
        
        stats = self.deduper.get_stats()
        self.assertEqual(stats["total_input"], 0)
        self.assertEqual(stats["unique_leads"], 0)
    
    def test_add_emails_to_lead(self):
        """Test adding emails to existing lead."""
        lead = Lead(
            place_id="test",
            name="Test",
            address="",
            emails=["existing@test.com"],
        )
        
        self.deduper.add_emails_to_lead(
            lead,
            ["new@test.com", "existing@test.com"],  # One new, one existing
            {"new@test.com": "personal"}
        )
        
        self.assertEqual(len(lead.emails), 2)
        self.assertIn("new@test.com", lead.emails)
        self.assertEqual(lead.email_quality.get("new@test.com"), "personal")


if __name__ == "__main__":
    unittest.main()

