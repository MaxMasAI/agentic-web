"""
tests/test_github_service.py - Unit tests for GitHub REST API Service
"""

import unittest
import base64
from unittest.mock import patch, MagicMock
from services.github_service import GitHubService


class TestGitHubService(unittest.TestCase):
    def setUp(self):
        self.service = GitHubService(token="test_gh_token_123")

    @patch("requests.Session.request")
    def test_get_authenticated_user(self, mock_req):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"login": "octocat", "id": 1}
        mock_req.return_value = mock_resp

        res = self.service.get_authenticated_user()
        self.assertTrue(res["success"])
        self.assertEqual(res["data"]["login"], "octocat")

    @patch("requests.Session.request")
    def test_create_and_delete_repo(self, mock_req):
        mock_resp = MagicMock()
        mock_resp.status_code = 201
        mock_resp.json.return_value = {"name": "test-repo", "owner": {"login": "octocat"}}
        mock_req.return_value = mock_resp

        create_res = self.service.create_repository("test-repo", private=True)
        self.assertTrue(create_res["success"])

        mock_del = MagicMock()
        mock_del.status_code = 204
        mock_req.return_value = mock_del
        del_res = self.service.delete_repository("octocat", "test-repo")
        self.assertTrue(del_res["success"])

    @patch("requests.Session.request")
    def test_get_and_upload_file(self, mock_req):
        # 1. Get file content with base64 decode
        raw_b64 = base64.b64encode(b"print('hello world')").decode("utf-8")
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "name": "main.py",
            "path": "main.py",
            "sha": "sha_12345",
            "encoding": "base64",
            "content": raw_b64
        }
        mock_req.return_value = mock_resp

        get_res = self.service.get_file_content("octocat", "test-repo", "main.py")
        self.assertTrue(get_res["success"])
        self.assertEqual(get_res["file_data"]["decoded_content"], "print('hello world')")

        # 2. Upload/Update file
        mock_put_resp = MagicMock()
        mock_put_resp.status_code = 200
        mock_put_resp.json.return_value = {"content": {"sha": "sha_67890"}}
        mock_req.return_value = mock_put_resp

        up_res = self.service.upload_or_update_file("octocat", "test-repo", "main.py", "new content", sha="sha_12345")
        self.assertTrue(up_res["success"])

    @patch("requests.Session.request")
    def test_issues_and_pull_requests(self, mock_req):
        # 1. Create issue
        mock_resp = MagicMock()
        mock_resp.status_code = 201
        mock_resp.json.return_value = {"number": 10, "title": "New Bug"}
        mock_req.return_value = mock_resp

        issue_res = self.service.create_issue("octocat", "test-repo", "New Bug")
        self.assertTrue(issue_res["success"])
        self.assertEqual(issue_res["data"]["number"], 10)

        # 2. Comment issue
        mock_c_resp = MagicMock()
        mock_c_resp.status_code = 201
        mock_c_resp.json.return_value = {"id": 101, "body": "Fixed in commit abc"}
        mock_req.return_value = mock_c_resp

        c_res = self.service.comment_issue("octocat", "test-repo", 10, "Fixed in commit abc")
        self.assertTrue(c_res["success"])

        # 3. Create PR
        mock_pr_resp = MagicMock()
        mock_pr_resp.status_code = 201
        mock_pr_resp.json.return_value = {"number": 1, "state": "open"}
        mock_req.return_value = mock_pr_resp

        pr_res = self.service.create_pull_request("octocat", "test-repo", "Feature PR", "feature-branch")
        self.assertTrue(pr_res["success"])


if __name__ == "__main__":
    unittest.main()
