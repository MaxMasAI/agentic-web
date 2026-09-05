"""
tests/test_facebook_service.py - Unit tests for Facebook Graph API service
"""

import unittest
from unittest.mock import patch, MagicMock
from services.facebook_service import FacebookService


class TestFacebookService(unittest.TestCase):
    def setUp(self):
        self.service = FacebookService(user_access_token="test_fb_token_123", default_page_id="page_999")

    @patch("requests.get")
    def test_get_user_info(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"id": "user_123", "name": "Sahil Kumar"}
        mock_get.return_value = mock_resp

        res = self.service.get_user_info()
        self.assertTrue(res["success"])
        self.assertEqual(res["data"]["name"], "Sahil Kumar")

    @patch("requests.get")
    def test_list_pages_and_set_default(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "data": [
                {"id": "page_101", "name": "AI Tech Hub", "access_token": "page_tok_101"}
            ]
        }
        mock_get.return_value = mock_resp

        res = self.service.list_pages()
        self.assertTrue(res["success"])
        self.assertEqual(len(res["data"]["data"]), 1)

        set_res = self.service.set_default_page("page_101")
        self.assertTrue(set_res["success"])
        self.assertEqual(self.service.default_page_id, "page_101")

    @patch("requests.post")
    def test_create_post_and_upload_photo(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"id": "page_999_post_555"}
        mock_post.return_value = mock_resp

        post_res = self.service.create_page_post("Hello from Agentic Web!")
        self.assertTrue(post_res["success"])
        self.assertEqual(post_res["data"]["id"], "page_999_post_555")

        photo_res = self.service.upload_photo("https://example.com/banner.png", caption="Awesome photo")
        self.assertTrue(photo_res["success"])

    @patch("requests.delete")
    def test_delete_page_post(self, mock_delete):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"success": True}
        mock_delete.return_value = mock_resp

        del_res = self.service.delete_page_post("page_999_post_555")
        self.assertTrue(del_res["success"])


if __name__ == "__main__":
    unittest.main()
