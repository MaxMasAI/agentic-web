"""
tests/test_wikipedia_service.py - Unit tests for Wikipedia Plugin Service
"""

import unittest
from unittest.mock import patch, MagicMock
from services.wikipedia_service import WikipediaService


class TestWikipediaService(unittest.TestCase):
    def setUp(self):
        self.service = WikipediaService(language="en")

    def test_language_controls(self):
        res = self.service.set_language("pl")
        self.assertTrue(res["success"])
        self.assertEqual(self.service.language, "pl")

        lang = self.service.get_language()
        self.assertEqual(lang["language"], "pl")

        supported = self.service.list_supported_languages()
        self.assertIn("en", supported["languages"])
        self.assertIn("es", supported["languages"])

    @patch("requests.Session.get")
    def test_search_articles(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "query": {
                "search": [
                    {"title": "Artificial Intelligence", "snippet": "AI is the simulation of human intelligence.", "pageid": 111}
                ]
            }
        }
        mock_get.return_value = mock_resp

        res = self.service.search_articles("AI")
        self.assertTrue(res["success"])
        self.assertEqual(len(res["results"]), 1)
        self.assertEqual(res["results"][0]["title"], "Artificial Intelligence")

    @patch("requests.Session.get")
    def test_get_summary_and_random(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "title": "Machine Learning",
            "extract": "Machine learning is a field of study in artificial intelligence.",
            "description": "Scientific study of algorithms and statistical models"
        }
        mock_get.return_value = mock_resp

        sum_res = self.service.get_article_summary("Machine Learning")
        self.assertTrue(sum_res["success"])
        self.assertEqual(sum_res["title"], "Machine Learning")

        rnd_res = self.service.get_random_article()
        self.assertTrue(rnd_res["success"])


if __name__ == "__main__":
    unittest.main()
