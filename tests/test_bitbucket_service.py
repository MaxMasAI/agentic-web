"""
tests/test_bitbucket_service.py - Unit tests for Bitbucket Cloud API integration
"""

import unittest
from unittest.mock import patch, MagicMock
from services.bitbucket_service import BitbucketService


class TestBitbucketService(unittest.TestCase):
    def setUp(self):
        self.service = BitbucketService(username="testuser", app_password="testpassword")

    @patch("requests.Session.request")
    def test_get_authenticated_user(self, mock_req):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"username": "testuser", "display_name": "Test User"}
        mock_req.return_value = mock_resp

        res = self.service.get_authenticated_user()
        self.assertTrue(res["success"])
        self.assertEqual(res["data"]["username"], "testuser")

    @patch("requests.Session.request")
    def test_list_workspaces(self, mock_req):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"values": [{"slug": "my-workspace", "name": "My Workspace"}]}
        mock_req.return_value = mock_resp

        res = self.service.list_workspaces()
        self.assertTrue(res["success"])
        self.assertEqual(len(res["data"]["values"]), 1)

    @patch("requests.Session.request")
    def test_create_and_delete_repository(self, mock_req):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"name": "new-repo", "slug": "new-repo"}
        mock_req.return_value = mock_resp

        create_res = self.service.create_repository("my-workspace", "new-repo", is_private=True)
        self.assertTrue(create_res["success"])

        mock_del = MagicMock()
        mock_del.status_code = 204
        mock_req.return_value = mock_del
        del_res = self.service.delete_repository("my-workspace", "new-repo")
        self.assertTrue(del_res["success"])

    @patch("requests.Session.request")
    def test_create_issue_and_pull_request(self, mock_req):
        mock_resp = MagicMock()
        mock_resp.status_code = 201
        mock_resp.json.return_value = {"id": 1, "title": "Fix memory leak"}
        mock_req.return_value = mock_resp

        issue_res = self.service.create_issue("my-workspace", "new-repo", "Fix memory leak")
        self.assertTrue(issue_res["success"])

        pr_res = self.service.create_pull_request("my-workspace", "new-repo", "Merge feature", "feature-branch")
        self.assertTrue(pr_res["success"])

    @patch("requests.Session.request")
    def test_merge_pull_request(self, mock_req):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"state": "MERGED"}
        mock_req.return_value = mock_resp

        res = self.service.merge_pull_request("my-workspace", "new-repo", 1)
        self.assertTrue(res["success"])
        self.assertEqual(res["data"]["state"], "MERGED")


if __name__ == "__main__":
    unittest.main()
