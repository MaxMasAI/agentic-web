"""
tests/test_telegram_service.py - Unit tests for Telegram Plugin Service (Bot & User mode)
"""

import unittest
from unittest.mock import patch, MagicMock
from services.telegram_service import TelegramService


class TestTelegramService(unittest.TestCase):
    def setUp(self):
        self.service = TelegramService(bot_token="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11", default_chat_id="999888")

    @patch("requests.Session.request")
    def test_send_message_and_photo(self, mock_req):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"ok": True, "result": {"message_id": 101, "text": "Hello Telegram"}}
        mock_req.return_value = mock_resp

        res_msg = self.service.send_message("Hello Telegram")
        self.assertTrue(res_msg["success"])
        self.assertEqual(res_msg["result"]["message_id"], 101)

        res_photo = self.service.send_photo("https://example.com/image.jpg", caption="Test photo")
        self.assertTrue(res_photo["success"])

    @patch("requests.Session.request")
    def test_get_chat_and_updates(self, mock_req):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"ok": True, "result": {"id": 999888, "title": "Dev Channel"}}
        mock_req.return_value = mock_resp

        chat_res = self.service.get_chat()
        self.assertTrue(chat_res["success"])
        self.assertEqual(chat_res["result"]["title"], "Dev Channel")

        mock_resp.json.return_value = {"ok": True, "result": [{"update_id": 1}]}
        up_res = self.service.get_updates()
        self.assertTrue(up_res["success"])

    def test_user_mode_operations(self):
        contacts = self.service.list_contacts()
        self.assertTrue(contacts["success"])
        self.assertEqual(contacts["mode"], "user_mode")

        dialogs = self.service.list_dialogs()
        self.assertTrue(dialogs["success"])

        history = self.service.get_chat_history(1001)
        self.assertTrue(history["success"])
        self.assertEqual(len(history["messages"]), 2)


if __name__ == "__main__":
    unittest.main()
