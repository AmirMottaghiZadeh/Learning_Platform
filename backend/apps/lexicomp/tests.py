import sqlite3
import tempfile
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from . import services


def _make_snapshot(directory: str):
    """A minimal interact.db: warfarin + aspirin interact two ways (a
    specific rule and a broader class-level one); ibuprofen's only rule is
    excepted for this specific generic, so it should never surface."""
    d = Path(directory)
    conn = sqlite3.connect(d / "interact.db")
    conn.executescript(
        """
        CREATE TABLE generic (id integer primary key, name text, combination integer default 0);
        CREATE TABLE brand (id integer primary key, generic_id integer, name text);
        CREATE TABLE category (id integer primary key, name text);
        CREATE TABLE category_generic_xref (category_id integer, generic_id integer);
        CREATE TABLE monograph (
            id integer primary key, object_id integer, precipitant_id integer,
            severity_id integer, reliability_id integer,
            summary text, management text, discussion text, footnotes text
        );
        CREATE TABLE severity (id integer primary key, severity text);
        CREATE TABLE reliability (id integer primary key, reliability text);
        CREATE TABLE monograph_generic_exception_xref (
            monograph_id integer, category_id integer, generic_id integer
        );
        """
    )
    conn.executemany(
        "INSERT INTO generic VALUES (?,?,?)",
        [(1, "Warfarin", 0), (2, "Aspirin", 0), (3, "Ibuprofen", 0)],
    )
    conn.executemany(
        "INSERT INTO brand VALUES (?,?,?)",
        [(1, 2, "Ecotrin (Aspirin)")],
    )
    conn.executemany(
        "INSERT INTO category VALUES (?,?)",
        [
            (1, "Warfarin"), (2, "Aspirin"), (3, "Ibuprofen"),
            (10, "Vitamin K Antagonists"), (11, "Salicylates"), (12, "Anticoagulants"),
            (13, "NSAIDs"),
        ],
    )
    conn.executemany(
        "INSERT INTO category_generic_xref VALUES (?,?)",
        [
            (1, 1), (10, 1), (12, 1),   # warfarin: itself, VKA, anticoagulant
            (2, 2), (11, 2),            # aspirin: itself, salicylate
            (3, 3), (13, 3),            # ibuprofen: itself, NSAID
        ],
    )
    conn.executemany(
        "INSERT INTO severity VALUES (?,?)",
        [(1, "Major"), (2, "Moderate"), (3, "Minor")],
    )
    conn.executemany(
        "INSERT INTO reliability VALUES (?,?)",
        [(1, "Established")],
    )
    conn.executemany(
        "INSERT INTO monograph VALUES (?,?,?,?,?,?,?,?,?)",
        [
            (100, 10, 2, 1, 1, "Aspirin increases anticoagulant effect.", "Monitor INR.", "Discussion.", ""),
            (101, 11, 12, 2, 1, "Salicylates increase anticoagulant effect.", "Monitor.", "Discussion.", ""),
            (102, 13, 12, 2, 1, "NSAIDs increase anticoagulant effect.", "Avoid.", "Discussion.", ""),
        ],
    )
    # The NSAID x anticoagulant rule (102) doesn't apply when the NSAID is
    # specifically ibuprofen (generic 3) filling the object role (category 13).
    conn.executemany(
        "INSERT INTO monograph_generic_exception_xref VALUES (?,?,?)",
        [(102, 13, 3)],
    )
    conn.commit()
    conn.close()


class LexicompServiceTests(TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.addCleanup(services.close_all)
        _make_snapshot(self._tmp.name)

    def _with_snapshot(self):
        return override_settings(LEXICOMP_DB_DIR=self._tmp.name)

    def test_search_matches_generic_and_brand_names(self):
        with self._with_snapshot():
            results = services.search_drugs("aspirin")
        kinds = {r["kind"] for r in results}
        self.assertEqual(kinds, {"generic", "brand"})
        self.assertTrue(all(r["generic_id"] == 2 for r in results))

    def test_search_without_query_is_empty(self):
        with self._with_snapshot():
            self.assertEqual(services.search_drugs(""), [])

    def test_single_drug_has_no_interactions(self):
        with self._with_snapshot():
            self.assertEqual(services.check_interactions([1]), [])

    def test_warfarin_and_aspirin_interact_two_ways_sorted_by_severity(self):
        with self._with_snapshot():
            results = services.check_interactions([1, 2])
        self.assertEqual([r["monograph_id"] for r in results], [100, 101])
        self.assertEqual(results[0]["severity"], "Major")
        self.assertEqual(results[0]["object_name"], "Warfarin")
        self.assertEqual(results[0]["precipitant_name"], "Aspirin")

    def test_exception_suppresses_the_specific_excepted_generic(self):
        with self._with_snapshot():
            results = services.check_interactions([1, 3])
        self.assertEqual(results, [])

    def test_unaffected_pair_has_no_interactions(self):
        with self._with_snapshot():
            results = services.check_interactions([2, 3])
        self.assertEqual(results, [])


class LexicompApiTests(TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.addCleanup(services.close_all)
        _make_snapshot(self._tmp.name)
        self.client = APIClient()
        self.client.force_authenticate(
            get_user_model().objects.create_user("u", "u@e.com", "x")
        )

    def _with_snapshot(self):
        return override_settings(LEXICOMP_DB_DIR=self._tmp.name)

    def test_drug_search_endpoint(self):
        with self._with_snapshot():
            res = self.client.get("/api/v1/lexicomp/drugs/", {"search": "warfarin"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data[0]["name"], "Warfarin")

    def test_interaction_check_endpoint(self):
        with self._with_snapshot():
            res = self.client.post(
                "/api/v1/lexicomp/interactions/", {"generic_ids": [1, 2]}, format="json"
            )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 2)

    def test_interaction_check_requires_at_least_two_drugs(self):
        with self._with_snapshot():
            res = self.client.post(
                "/api/v1/lexicomp/interactions/", {"generic_ids": [1]}, format="json"
            )
        self.assertEqual(res.status_code, 400)

    def test_unavailable_snapshot_answers_503(self):
        services.close_all()
        with override_settings(LEXICOMP_DB_DIR="/nonexistent/path"):
            res = self.client.get("/api/v1/lexicomp/drugs/", {"search": "x"})
        self.assertEqual(res.status_code, 503)
        self.assertEqual(res.data["code"], "FEATURE_NOT_AVAILABLE")

    def test_requires_authentication(self):
        with self._with_snapshot():
            res = APIClient().get("/api/v1/lexicomp/drugs/", {"search": "x"})
        self.assertEqual(res.status_code, 401)
