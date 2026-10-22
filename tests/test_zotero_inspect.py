import importlib.util
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    "zotero_inspect", Path(__file__).resolve().parents[1] / "scripts" / "zotero_inspect.py"
)
bridge = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bridge)


class InspectTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.db = sqlite3.connect(self.root / "zotero.sqlite")
        self.db.executescript("""
            CREATE TABLE libraries(libraryID INTEGER,type TEXT);
            CREATE TABLE collections(collectionID INTEGER,key TEXT,libraryID INTEGER,collectionName TEXT);
            CREATE TABLE deletedCollections(collectionID INTEGER);
            CREATE TABLE items(itemID INTEGER,key TEXT,libraryID INTEGER);
            CREATE TABLE itemData(itemID INTEGER,fieldID INTEGER,valueID INTEGER);
            CREATE TABLE fields(fieldID INTEGER,fieldName TEXT);
            CREATE TABLE itemDataValues(valueID INTEGER,value TEXT);
            CREATE TABLE deletedItems(itemID INTEGER);
            CREATE TABLE itemAttachments(itemID INTEGER,parentItemID INTEGER,contentType TEXT,path TEXT);
            CREATE TABLE collectionItems(collectionID INTEGER,itemID INTEGER);
            INSERT INTO libraries VALUES(7,'user');
            INSERT INTO collections VALUES(12,'COLLTEST',7,'Spectra');
            INSERT INTO fields VALUES(1,'title'),(2,'DOI'),(3,'extra');
            INSERT INTO items VALUES(1,'PARENT01',7),(2,'PDFKEY01',7);
            INSERT INTO itemDataValues VALUES(1,'A Raman Study'),(2,'https://doi.org/10.1234/ABC'),(3,'arXiv: 2601.12345v2');
            INSERT INTO itemData VALUES(1,1,1),(1,2,2),(1,3,3);
            INSERT INTO itemAttachments VALUES(2,1,'application/pdf','storage:paper.pdf');
            INSERT INTO collectionItems VALUES(12,1);
        """)
        self.db.commit()
        attachment = self.root / "storage" / "PDFKEY01"
        attachment.mkdir(parents=True)
        (attachment / "paper.pdf").write_bytes(b"%PDF-1.7\nnot a complete PDF")

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def inspect(self, **kwargs):
        return bridge.inspect(self.root, collection_name="Spectra", **kwargs)

    def test_doi_identity_reuses_parent_and_distinguishes_attachment_key(self):
        result = self.inspect(doi="DOI:10.1234/abc")
        item = result["candidates"][0]
        self.assertEqual(result["candidate_count"], 1)
        self.assertEqual(item["key"], "PARENT01")
        self.assertEqual(item["pdfs"][0]["key"], "PDFKEY01")
        self.assertTrue(item["in_target_collection"])
        self.assertTrue(item["pdfs"][0]["pdf_header_valid"])
        self.assertFalse(item["pdfs"][0]["content_verified"])

    def test_preprint_version_matches_existing_journal_record(self):
        item = self.inspect(arxiv_id="https://arxiv.org/pdf/2601.12345v1.pdf")["candidates"][0]
        self.assertEqual(item["key"], "PARENT01")
        self.assertIn("arxiv", item["match_basis"])

    def test_existing_item_outside_collection_is_not_marked_complete(self):
        self.db.execute("DELETE FROM collectionItems")
        self.db.commit()
        item = self.inspect(doi="10.1234/abc")["candidates"][0]
        self.assertFalse(item["in_target_collection"])

    def test_ambiguous_collection_stops_instead_of_selecting_first(self):
        self.db.execute("INSERT INTO collections VALUES(13,'OTHERKEY',7,'Spectra')")
        self.db.commit()
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            self.inspect(doi="10.1234/abc")

    def test_deleted_items_are_not_reused(self):
        self.db.execute("INSERT INTO deletedItems VALUES(1)")
        self.db.commit()
        self.assertEqual(self.inspect(doi="10.1234/abc")["candidate_count"], 0)

    def test_wal_commits_are_included_without_writing_source(self):
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("UPDATE itemDataValues SET value='10.1234/WAL' WHERE valueID=2")
        self.db.commit()
        before = bridge.signature(self.root / "zotero.sqlite")
        self.assertEqual(self.inspect(doi="10.1234/wal")["candidate_count"], 1)
        self.assertEqual(before, bridge.signature(self.root / "zotero.sqlite"))

    def test_title_only_match_is_explicitly_provisional(self):
        item = self.inspect(title="Ａ Raman—Study")["candidates"][0]
        self.assertEqual(item["match_basis"], ["title_candidate_requires_author_year_check"])

    def test_snapshot_change_stops_before_query(self):
        with patch.object(bridge, "signature", side_effect=[[(True, 1, 1)], [(True, 2, 2)]]):
            with self.assertRaisesRegex(ValueError, "snapshot_unstable"):
                self.inspect(doi="10.1234/abc")

    def test_storage_path_traversal_is_not_read(self):
        self.assertIsNone(bridge.attachment_path(self.root, "PDFKEY01", "storage:../../secret.pdf"))

    def test_missing_file_is_distinct_from_existing_attachment(self):
        (self.root / "storage" / "PDFKEY01" / "paper.pdf").unlink()
        attachment = self.inspect(doi="10.1234/abc")["candidates"][0]["pdfs"][0]
        self.assertFalse(attachment["local_exists"])
        self.assertFalse(attachment["pdf_header_valid"])

    def test_status_rejects_remote_service(self):
        with self.assertRaises(ValueError):
            bridge.status("https://example.com")


if __name__ == "__main__":
    unittest.main()
