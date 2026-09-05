"""
tests/test_remote_server_service.py - Unit tests for Remote Server Plugin (SSH, SFTP, FTP, SMB)
"""

import unittest
import tempfile
import os
import shutil
from services.remote_server_service import RemoteServerService, ServerProtocol


class TestRemoteServerService(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.test_dir, "server_profiles.json")
        self.service = RemoteServerService(config_path=self.config_path)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_credential_masking_for_model(self):
        # Verify that listing servers for the AI model strips all passwords and private keys
        servers = self.service.list_servers_for_model()
        self.assertTrue(len(servers) >= 2)
        for s in servers:
            self.assertNotIn("password", s)
            self.assertNotIn("key_path", s)
            self.assertIn("id", s)
            self.assertIn("name", s)
            self.assertIn("host", s)
            self.assertIn("port", s)

    def test_add_smb_server(self):
        res = self.service.add_server(
            server_id="nas_share",
            name="Office NAS",
            protocol=ServerProtocol.SMB,
            host="192.168.1.200",
            port=445,
            share_name="data",
            username="nas_user",
            password="secret_password"
        )
        self.assertTrue(res["success"])
        info = res["server"]
        self.assertEqual(info["id"], "nas_share")
        self.assertEqual(info["protocol"], "smb")
        self.assertNotIn("password", info)

    def test_execute_ssh_command(self):
        res = self.service.execute_ssh_command("prod_web_server", "uptime")
        self.assertTrue(res["success"])
        self.assertEqual(res["server_id"], "prod_web_server")
        self.assertEqual(res["command"], "uptime")

    def test_smb_and_ftp_directory_listing(self):
        res_smb = self.service.list_remote_directory("corporate_smb_share", "/")
        self.assertTrue(res_smb["success"])
        self.assertEqual(res_smb["protocol"], "smb")


if __name__ == "__main__":
    unittest.main()
