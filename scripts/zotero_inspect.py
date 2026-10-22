#!/usr/bin/env python3
"""Read-only Zotero connection and duplicate/collection inspection (stdlib)."""
import argparse
from contextlib import contextmanager
import json
from pathlib import Path
import re
import shutil
import sqlite3
import tempfile
import unicodedata
import urllib.error
import urllib.parse
import urllib.request


def normalize_doi(value):
    value = (value or "").strip()
    value = re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", "", value, flags=re.I)
    return value.casefold()


def normalize_arxiv(value):
    value = (value or "").strip()
    value = re.sub(r"^(?:https?://(?:export\.)?arxiv\.org/(?:abs|pdf)/|arxiv:\s*)", "", value, flags=re.I)
    value = re.sub(r"\.pdf$", "", value, flags=re.I)
    return re.sub(r"v\d+$", "", value, flags=re.I).casefold()


def normalize_title(value):
    return "".join(c for c in unicodedata.normalize("NFKC", value or "").casefold() if c.isalnum())


def signature(database):
    paths = [database, Path(str(database) + "-wal")]
    return [(p.exists(), p.stat().st_size if p.exists() else None,
             p.stat().st_mtime_ns if p.exists() else None) for p in paths]


@contextmanager
def snapshot(data_dir):
    database = Path(data_dir).expanduser().resolve() / "zotero.sqlite"
    if not database.is_file():
        raise ValueError("zotero.sqlite not found in the explicitly selected data directory")
    with tempfile.TemporaryDirectory(prefix="research-radar-read-") as folder:
        before = signature(database)
        for source in [database, Path(str(database) + "-wal")]:
            if source.exists():
                shutil.copyfile(source, Path(folder) / source.name)
        if signature(database) != before:
            raise ValueError("snapshot_unstable: source changed during copying; do not create new items")
        connection = sqlite3.connect((Path(folder) / database.name).as_uri() + "?mode=ro", uri=True)
        try:
            connection.execute("PRAGMA query_only=ON")
            if connection.execute("PRAGMA quick_check").fetchone()[0] != "ok":
                raise ValueError("snapshot_invalid: database consistency check failed")
            yield connection, database.parent
        finally:
            connection.close()


def attachment_path(root, key, stored_path, attachment_base=None):
    if not stored_path:
        return None
    if stored_path.startswith("storage:"):
        base = (root / "storage" / key).resolve()
        candidate = (base / stored_path[len("storage:"):]).resolve()
        if not candidate.is_relative_to(base):
            return None
        return candidate
    if stored_path.startswith("attachments:"):
        if not attachment_base:
            return None
        base = Path(attachment_base).expanduser().resolve()
        candidate = (base / stored_path[len("attachments:"):]).resolve()
        return candidate if candidate.is_relative_to(base) else None
    candidate = Path(stored_path)
    return candidate if candidate.is_absolute() else None


def inspect(data_dir, *, doi=None, arxiv_id=None, title=None,
            collection_key=None, collection_name=None, attachment_base=None):
    if not any([normalize_doi(doi), normalize_arxiv(arxiv_id), normalize_title(title)]):
        raise ValueError("Provide at least one DOI, arXiv ID or title")
    if not any([collection_key, collection_name]):
        raise ValueError("Provide the confirmed target collection key or name")
    with snapshot(data_dir) as (db, root):
        users = db.execute("SELECT libraryID FROM libraries WHERE type='user'").fetchall()
        if len(users) != 1:
            raise ValueError("Personal library could not be identified uniquely")
        library = users[0][0]
        collections = db.execute(
            "SELECT collectionID,key,collectionName FROM collections WHERE libraryID=?", (library,)
        ).fetchall()
        tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        deleted_collections = set()
        if "deletedCollections" in tables:
            deleted_collections = {r[0] for r in db.execute("SELECT collectionID FROM deletedCollections")}
        target = [r for r in collections if r[0] not in deleted_collections and
                  (r[1] == collection_key if collection_key else r[2] == collection_name)]
        if len(target) != 1:
            raise ValueError("target_collection_missing_or_ambiguous")
        cid, ckey, cname = target[0]
        if collection_name and cname != collection_name:
            raise ValueError("Target key no longer matches the configured collection name")
        rows = db.execute("""
            SELECT i.itemID,i.key,f.fieldName,v.value
            FROM items i JOIN itemData d ON i.itemID=d.itemID
            JOIN fields f ON f.fieldID=d.fieldID
            JOIN itemDataValues v ON v.valueID=d.valueID
            WHERE i.libraryID=? AND i.itemID NOT IN (SELECT itemID FROM deletedItems)
            AND i.itemID NOT IN (SELECT itemID FROM itemAttachments)
            AND f.fieldName IN ('title','DOI','url','extra','archiveLocation','date')
        """, (library,)).fetchall()
        items = {}
        for iid, key, field, value in rows:
            items.setdefault(iid, {"key": key, "data": {}})["data"][field] = value
        candidates = []
        for iid, item in items.items():
            data = item["data"]
            basis = []
            if doi and normalize_doi(doi) == normalize_doi(data.get("DOI")):
                basis.append("doi")
            if arxiv_id:
                text = " ".join(str(data.get(f, "")) for f in ("url", "extra", "archiveLocation"))
                ids = re.findall(r"(?:arxiv:\s*|arxiv\.org/(?:abs|pdf)/)(\d{4}\.\d{4,5}(?:v\d+)?)", text, re.I)
                if data.get("archiveLocation"):
                    ids.append(data["archiveLocation"])
                if normalize_arxiv(arxiv_id) in {normalize_arxiv(x) for x in ids}:
                    basis.append("arxiv")
            if title and normalize_title(title) == normalize_title(data.get("title")):
                basis.append("title_candidate_requires_author_year_check")
            if not basis:
                continue
            member = bool(db.execute(
                "SELECT 1 FROM collectionItems WHERE itemID=? AND collectionID=?", (iid, cid)
            ).fetchone())
            attachments = []
            for akey, path in db.execute("""
                SELECT i.key,a.path FROM itemAttachments a JOIN items i ON i.itemID=a.itemID
                WHERE a.parentItemID=? AND a.contentType='application/pdf'
                AND i.itemID NOT IN (SELECT itemID FROM deletedItems)
            """, (iid,)):
                local = attachment_path(root, akey, path, attachment_base)
                exists = bool(local and local.is_file())
                header = False
                if exists:
                    try:
                        with local.open("rb") as stream:
                            header = stream.read(5) == b"%PDF-"
                    except OSError:
                        exists = False
                attachments.append({"key": akey, "local_exists": exists,
                                    "pdf_header_valid": header, "content_verified": False,
                                    "uri": "zotero://open-pdf/library/items/" + akey})
            candidates.append({"key": item["key"], "title": data.get("title"),
                               "doi": data.get("DOI"), "date": data.get("date"),
                               "match_basis": basis, "in_target_collection": member,
                               "uri": "zotero://select/library/items/" + item["key"],
                               "pdfs": attachments})
        return {"source": "read_only_database_snapshot", "library_id": library,
                "collection": {"key": ckey, "name": cname, "local_id": cid},
                "candidate_count": len(candidates), "candidates": candidates}


def status(base_url):
    parsed = urllib.parse.urlparse(base_url)
    if parsed.scheme != "http" or parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
        raise ValueError("Only the local Zotero HTTP service is supported")
    result = {}
    for name, route in [("connector", "/connector/ping"), ("local_api", "/api/")]:
        request = urllib.request.Request(base_url.rstrip("/") + route,
                                         headers={"Zotero-API-Version": "3"})
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                result[name] = {"status": response.status}
        except urllib.error.HTTPError as error:
            result[name] = {"status": error.code}
        except OSError as error:
            result[name] = {"status": None, "error_type": type(error).__name__}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    probe = commands.add_parser("status")
    probe.add_argument("--base-url", default="http://127.0.0.1:23119")
    lookup = commands.add_parser("inspect")
    lookup.add_argument("--data-dir", required=True)
    for field in ["doi", "arxiv-id", "title", "collection-key", "collection-name", "attachment-base"]:
        lookup.add_argument("--" + field)
    args = vars(parser.parse_args())
    command = args.pop("command")
    try:
        result = status(**args) if command == "status" else inspect(**args)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, OSError, sqlite3.Error) as error:
        print(json.dumps({"error": str(error), "safe_to_create": False}, ensure_ascii=False))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
