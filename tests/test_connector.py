"""Offline review checks. No real Reddit credentials or API calls."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from backend.discovery import build_discovery, fetch_reddit, valid_reddit_url, NoRedirect
from backend.reddit_auth import get_access_token


class ConnectorChecks(unittest.TestCase):
    def test_pending_approval_cannot_request_listings(self):
        with patch.dict('os.environ', {'REDDIT_USAGE_APPROVED': '', 'REDDIT_ACCESS_TOKEN': ''}), patch('backend.reddit_auth.get_access_token', return_value=(None, 'Pending approval')), patch('urllib.request.build_opener') as network:
            self.assertEqual(fetch_reddit(), ([], 'Pending approval'))
            network.assert_not_called()

    def test_missing_credentials_cannot_refresh_token(self):
        with tempfile.TemporaryDirectory() as directory, patch('backend.reddit_auth.token_request') as network:
            self.assertIsNone(get_access_token(Path(directory))[0])
            network.assert_not_called()

    def test_social_import_cannot_authorize_or_verify(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'config').mkdir()
            lead = {'url': 'https://www.reddit.com/r/stocks/comments/abc123/example/', 'symbols': ['NVDA', 'UNKNOWN'], 'fact_verified': True, 'execution_authorized': True}
            (root / 'config/discovery_leads.json').write_text(json.dumps({'leads': [lead, lead]}), encoding='utf-8')
            result = build_discovery({}, root)
            self.assertEqual(len(result['leads']), 1)
            self.assertEqual(result['leads'][0]['symbols'], ['NVDA'])
            self.assertFalse(result['leads'][0]['fact_verified'])
            self.assertFalse(result['leads'][0]['execution_authorized'])

    def test_urls_and_redirects_are_restricted(self):
        self.assertTrue(valid_reddit_url('https://www.reddit.com/r/stocks/comments/abc123/example/'))
        for url in ('http://www.reddit.com/r/stocks/comments/abc123/example/', 'https://reddit.com/login', 'https://reddit.com.evil.test/r/stocks/comments/abc123/example/'):
            self.assertFalse(valid_reddit_url(url))
        with self.assertRaises(ValueError):
            NoRedirect().redirect_request(None, None, None, None, None, None)


if __name__ == '__main__':
    unittest.main()
