"""Tests for email and phone extraction."""

import unittest
from lead_engine.extractor import (
    EmailExtractor,
    PhoneNormalizer,
    SocialLinkExtractor,
    extract_domain,
)


class TestEmailExtractor(unittest.TestCase):
    """Tests for EmailExtractor class."""
    
    def setUp(self):
        self.extractor = EmailExtractor()
    
    def test_extract_simple_email(self):
        """Test extracting a simple email."""
        text = "Contact us at info@acmecorp.com"
        emails = self.extractor.extract(text)
        self.assertEqual(emails, ["info@acmecorp.com"])
    
    def test_extract_multiple_emails(self):
        """Test extracting multiple emails."""
        text = "Email: john@acmecorp.com or support@acmecorp.com"
        emails = self.extractor.extract(text)
        self.assertIn("john@acmecorp.com", emails)
        self.assertIn("support@acmecorp.com", emails)
    
    def test_extract_mailto_link(self):
        """Test extracting from mailto link."""
        text = '<a href="mailto:contact@business.com">Contact</a>'
        emails = self.extractor.extract(text)
        self.assertEqual(emails, ["contact@business.com"])
    
    def test_ignore_invalid_tld(self):
        """Test ignoring emails with invalid TLDs."""
        text = "image@file.png style@sheet.css"
        emails = self.extractor.extract(text)
        self.assertEqual(emails, [])
    
    def test_ignore_placeholder_emails(self):
        """Test ignoring placeholder emails."""
        text = "your@email.com name@domain.com test@example.com"
        emails = self.extractor.extract(text)
        self.assertEqual(emails, [])
    
    def test_normalize_email(self):
        """Test email normalization."""
        text = "JOHN@ACMECORP.COM"
        emails = self.extractor.extract(text)
        self.assertEqual(emails, ["john@acmecorp.com"])
    
    def test_classify_generic_email(self):
        """Test classification of generic emails."""
        results = self.extractor.extract_with_quality("info@acmecorp.com contact@mybusiness.org")
        for email, quality in results:
            self.assertEqual(quality, "generic")
    
    def test_classify_personal_email(self):
        """Test classification of personal emails."""
        results = self.extractor.extract_with_quality("john.smith@acmecorp.com")
        for email, quality in results:
            self.assertEqual(quality, "personal")
    
    def test_extract_complex_html(self):
        """Test extraction from complex HTML."""
        html = """
        <html>
        <body>
            <p>Contact: <a href="mailto:sales@acme.com">sales@acme.com</a></p>
            <span>support@acme.com</span>
            <script>var x = "noreply@acme.com";</script>
        </body>
        </html>
        """
        emails = self.extractor.extract(html)
        self.assertIn("sales@acme.com", emails)
        self.assertIn("support@acme.com", emails)


class TestPhoneNormalizer(unittest.TestCase):
    """Tests for PhoneNormalizer class."""
    
    def setUp(self):
        self.normalizer = PhoneNormalizer()
    
    def test_normalize_us_phone(self):
        """Test normalizing US phone numbers."""
        phone = "(512) 555-1234"
        normalized = self.normalizer.normalize(phone)
        self.assertEqual(normalized, "5125551234")
    
    def test_normalize_with_country_code(self):
        """Test normalizing phone with country code."""
        phone = "+1 512-555-1234"
        normalized = self.normalizer.normalize(phone)
        self.assertEqual(normalized, "+15125551234")
    
    def test_normalize_international(self):
        """Test normalizing international phone."""
        phone = "+44 20 7946 0958"
        normalized = self.normalizer.normalize(phone)
        self.assertEqual(normalized, "+442079460958")
    
    def test_extract_phones_from_text(self):
        """Test extracting phones from text."""
        text = "Call us at (512) 555-1234 or 512.555.5678"
        phones = self.normalizer.extract(text)
        self.assertTrue(len(phones) >= 1)
    
    def test_format_us_phone(self):
        """Test formatting US phone for display."""
        formatted = self.normalizer.format_display("5125551234")
        self.assertEqual(formatted, "(512) 555-1234")
    
    def test_reject_invalid_phone(self):
        """Test rejecting invalid phone numbers."""
        # All same digit
        self.assertFalse(self.normalizer._is_valid("1111111111"))
        # Too short
        self.assertFalse(self.normalizer._is_valid("12345"))
        # Too long
        self.assertFalse(self.normalizer._is_valid("1234567890123456"))


class TestSocialLinkExtractor(unittest.TestCase):
    """Tests for SocialLinkExtractor class."""
    
    def setUp(self):
        self.extractor = SocialLinkExtractor()
    
    def test_extract_linkedin(self):
        """Test extracting LinkedIn links."""
        html = '<a href="https://www.linkedin.com/company/acme">LinkedIn</a>'
        social = self.extractor.extract(html)
        self.assertIn("linkedin", social)
        self.assertEqual(social["linkedin"], "https://www.linkedin.com/company/acme")
    
    def test_extract_facebook(self):
        """Test extracting Facebook links."""
        html = '<a href="https://facebook.com/acmecorp">FB</a>'
        social = self.extractor.extract(html)
        self.assertIn("facebook", social)
    
    def test_extract_instagram(self):
        """Test extracting Instagram links."""
        html = 'Follow us: https://www.instagram.com/acme_official'
        social = self.extractor.extract(html)
        self.assertIn("instagram", social)
    
    def test_ignore_share_links(self):
        """Test ignoring share/intent links."""
        html = '<a href="https://facebook.com/sharer.php?u=...">Share</a>'
        social = self.extractor.extract(html)
        self.assertNotIn("facebook", social)
    
    def test_extract_multiple_platforms(self):
        """Test extracting from multiple platforms."""
        html = """
        <a href="https://linkedin.com/company/test">LI</a>
        <a href="https://facebook.com/testpage">FB</a>
        <a href="https://instagram.com/test">IG</a>
        """
        social = self.extractor.extract(html)
        self.assertIn("linkedin", social)
        self.assertIn("facebook", social)
        self.assertIn("instagram", social)


class TestExtractDomain(unittest.TestCase):
    """Tests for extract_domain function."""
    
    def test_extract_from_full_url(self):
        """Test extracting domain from full URL."""
        url = "https://www.example.com/page"
        self.assertEqual(extract_domain(url), "example.com")
    
    def test_extract_without_scheme(self):
        """Test extracting from URL without scheme."""
        url = "www.example.com/page"
        self.assertEqual(extract_domain(url), "example.com")
    
    def test_extract_with_port(self):
        """Test extracting from URL with port."""
        url = "https://example.com:8080/page"
        self.assertEqual(extract_domain(url), "example.com")
    
    def test_extract_subdomain(self):
        """Test preserving subdomain."""
        url = "https://shop.example.com"
        # Note: Our implementation removes www. but keeps other subdomains
        domain = extract_domain(url)
        self.assertIn("example.com", domain)
    
    def test_handle_empty_url(self):
        """Test handling empty URL."""
        self.assertIsNone(extract_domain(""))
        self.assertIsNone(extract_domain(None))


if __name__ == "__main__":
    unittest.main()

