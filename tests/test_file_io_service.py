"""
tests/test_file_io_service.py - Unit tests for Files I/O Service
"""

import unittest
import os
import shutil
import tempfile
from services.file_io_service import FileIOService


class TestFileIOService(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.service = FileIOService(base_dir=self.test_dir)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_write_read_append(self):
        # 1. Write
        res_w = self.service.write_file("hello.txt", "Hello World")
        self.assertTrue(res_w["success"])

        # 2. Read
        res_r = self.service.read_file("hello.txt")
        self.assertTrue(res_r["success"])
        self.assertEqual(res_r["content"], "Hello World")

        # 3. Append
        res_a = self.service.append_file("hello.txt", " - Added text")
        self.assertTrue(res_a["success"])
        res_r2 = self.service.read_file("hello.txt")
        self.assertEqual(res_r2["content"], "Hello World - Added text")

    def test_collision_timestamp_prefixing(self):
        # Initial write
        self.service.write_file("report.txt", "Initial Draft", overwrite=True)

        # Collision write without overwrite
        res = self.service.write_file("report.txt", "Second Draft", overwrite=False)
        self.assertTrue(res["success"])
        self.assertTrue(res["renamed_with_prefix"])
        self.assertIn("report.txt", res["path"])
        self.assertNotEqual(os.path.basename(res["path"]), "report.txt")

    def test_list_and_search_files(self):
        self.service.write_file("sample.py", "print('hello from script')")
        self.service.write_file("notes.md", "Project Roadmap & Architecture")

        list_res = self.service.list_dir()
        self.assertTrue(list_res["success"])
        self.assertEqual(len(list_res["entries"]), 2)

        search_res = self.service.search_files("Roadmap")
        self.assertTrue(search_res["success"])
        self.assertEqual(len(search_res["matches"]), 1)
        self.assertEqual(search_res["matches"][0]["name"], "notes.md")

    def test_python_code_execution(self):
        code = "print(10 + 25)"
        exec_res = self.service.execute_python_code(code)
        self.assertTrue(exec_res["success"])
        self.assertIn("35", exec_res["stdout"])


if __name__ == "__main__":
    unittest.main()
