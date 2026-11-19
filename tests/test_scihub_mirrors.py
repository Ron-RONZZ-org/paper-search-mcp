import asyncio
import os
import tempfile
import unittest
from unittest.mock import patch

from paper_search_mcp import server

ENV_KEY = "PAPER_SEARCH_MCP_SCIHUB_MIRRORS"


def _mirror_env(value):
    return patch.dict(os.environ, {ENV_KEY: value}, clear=False)


class TestSciHubMirrorList(unittest.TestCase):
    def setUp(self):
        self._saved = os.environ.pop(ENV_KEY, None)
        os.environ.pop("SCIHUB_MIRRORS", None)

    def tearDown(self):
        os.environ.pop(ENV_KEY, None)
        os.environ.pop("SCIHUB_MIRRORS", None)
        if self._saved is not None:
            os.environ[ENV_KEY] = self._saved

    def test_preferred_mirror_comes_first_and_duplicates_are_removed(self):
        with _mirror_env("https://a.example,https://b.example/"):
            mirrors = server._scihub_mirrors("https://b.example/")
        self.assertEqual(mirrors, ["https://b.example", "https://a.example"])

    def test_builtin_order_is_used_without_an_env_override(self):
        mirrors = server._scihub_mirrors()
        self.assertEqual(
            mirrors,
            ["https://sci-hub.ru", "https://sci-hub.st", "https://sci-hub.se"],
        )

    def test_env_override_replaces_the_builtin_list(self):
        with _mirror_env("https://only.example"):
            mirrors = server._scihub_mirrors()
        self.assertEqual(mirrors, ["https://only.example"])


class TestSciHubMirrorFallback(unittest.TestCase):
    def setUp(self):
        self._saved = os.environ.pop(ENV_KEY, None)
        os.environ.pop("SCIHUB_MIRRORS", None)

    def tearDown(self):
        os.environ.pop(ENV_KEY, None)
        os.environ.pop("SCIHUB_MIRRORS", None)
        if self._saved is not None:
            os.environ[ENV_KEY] = self._saved

    def test_loop_falls_through_to_the_next_mirror(self):
        calls = []

        def fake_download(fetcher, identifier):
            calls.append(fetcher.base_url)
            if "a.example" in fetcher.base_url:
                return ""
            path = os.path.join(fetcher.output_dir, "ok.pdf")
            with open(path, "wb") as handle:
                handle.write(b"%PDF-1.7\nok")
            return path

        with tempfile.TemporaryDirectory() as save_path, _mirror_env(
            "https://a.example,https://b.example"
        ), patch.object(server.SciHubFetcher, "download_pdf", fake_download):
            result, errors = server._try_scihub_mirrors("10.1000/x", save_path)

        self.assertTrue(result.endswith("ok.pdf"))
        self.assertEqual(calls, ["https://a.example", "https://b.example"])
        self.assertEqual(len(errors), 1)
        self.assertIn("a.example", errors[0])

    def test_mismatched_pdf_is_deleted_and_the_next_mirror_is_tried(self):
        def fake_download(fetcher, identifier):
            name = "wrong.pdf" if "a.example" in fetcher.base_url else "right.pdf"
            path = os.path.join(fetcher.output_dir, name)
            with open(path, "wb") as handle:
                handle.write(b"%PDF-1.7\n")
            return path

        with tempfile.TemporaryDirectory() as save_path, _mirror_env(
            "https://a.example,https://b.example"
        ), patch.object(
            server.SciHubFetcher, "download_pdf", fake_download
        ), patch.object(
            server, "_pdf_matches_expected", side_effect=lambda path, *_: path.endswith("right.pdf")
        ):
            result, errors = server._try_scihub_mirrors(
                "10.1000/x", save_path, expected_title="T", expected_doi="10.1000/x"
            )

        self.assertTrue(result.endswith("right.pdf"))
        self.assertFalse(os.path.exists(os.path.join(save_path, "wrong.pdf")))
        self.assertTrue(any("did not match" in error for error in errors))

    def test_all_mirrors_failing_reports_each_one(self):
        with tempfile.TemporaryDirectory() as save_path, _mirror_env(
            "https://a.example,https://b.example"
        ), patch.object(server.SciHubFetcher, "download_pdf", return_value=""):
            result, errors = server._try_scihub_mirrors("10.1000/x", save_path)

        self.assertEqual(result, "")
        self.assertEqual(len(errors), 2)
        self.assertTrue(any("a.example" in error for error in errors))
        self.assertTrue(any("b.example" in error for error in errors))

    def test_download_scihub_returns_the_first_working_path(self):
        def fake_download(fetcher, identifier):
            path = os.path.join(fetcher.output_dir, "ok.pdf")
            with open(path, "wb") as handle:
                handle.write(b"%PDF-1.7\n")
            return path

        with tempfile.TemporaryDirectory() as save_path, _mirror_env(
            "https://a.example"
        ), patch.object(server.SciHubFetcher, "download_pdf", fake_download):
            result = asyncio.run(server.download_scihub("10.1000/x", save_path=save_path))

        self.assertTrue(result.endswith("ok.pdf"))

    def test_download_scihub_names_every_mirror_on_failure(self):
        with tempfile.TemporaryDirectory() as save_path, _mirror_env(
            "https://a.example,https://b.example"
        ), patch.object(server.SciHubFetcher, "download_pdf", return_value=""):
            result = asyncio.run(server.download_scihub("10.1000/x", save_path=save_path))

        self.assertIn("every mirror", result)
        self.assertIn("a.example", result)
        self.assertIn("b.example", result)


if __name__ == "__main__":
    unittest.main()
