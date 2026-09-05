"""
tests/test_google_suite_service.py - Unit tests for Google Suite Service (Gmail, Calendar, Drive, Docs, Maps, etc.)
"""

import unittest
from unittest.mock import patch, MagicMock
from services.google_suite_service import GoogleSuiteService


class TestGoogleSuiteService(unittest.TestCase):
    def setUp(self):
        self.service = GoogleSuiteService(access_token="mock_google_oauth_token", api_key="mock_key")

    @patch("requests.Session.request")
    def test_gmail_send_and_list(self, mock_req):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"messages": [{"id": "msg_123"}]}
        mock_req.return_value = mock_resp

        list_res = self.service.list_recent_emails(5)
        self.assertTrue(list_res["success"])
        self.assertEqual(len(list_res["data"]["messages"]), 1)

        send_res = self.service.send_email("test@example.com", "Subject", "Body content")
        self.assertTrue(send_res["success"])

    @patch("requests.Session.request")
    def test_calendar_events(self, mock_req):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"items": [{"id": "event_99", "summary": "Team Sync"}]}
        mock_req.return_value = mock_resp

        events_res = self.service.list_today_events()
        self.assertTrue(events_res["success"])
        self.assertEqual(events_res["data"]["items"][0]["summary"], "Team Sync")

    @patch("requests.Session.request")
    def test_drive_and_docs(self, mock_req):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"id": "doc_abc123", "title": "Project Specification"}
        mock_req.return_value = mock_resp

        doc_res = self.service.create_document("Project Specification")
        self.assertTrue(doc_res["success"])
        self.assertEqual(doc_res["data"]["title"], "Project Specification")

    @patch("requests.Session.request")
    def test_maps_geocode(self, mock_req):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"results": [{"formatted_address": "Mountain View, CA"}]}
        mock_req.return_value = mock_resp

        geo_res = self.service.geocode("1600 Amphitheatre Pkwy, Mountain View, CA")
        self.assertTrue(geo_res["success"])
        self.assertEqual(geo_res["data"]["results"][0]["formatted_address"], "Mountain View, CA")


if __name__ == "__main__":
    unittest.main()
