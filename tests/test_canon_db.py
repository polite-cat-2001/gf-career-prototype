from __future__ import annotations

import json
import sqlite3
from pathlib import Path

EXPECTED = {
    "countries": 106,
    "leagues": 279,
    "clubs": 4406,
    "players": 121927,
    "national_teams": 246,
    "stats_per_player": 22,
    "free_agents": 1895,
}


def connect(canon_db: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(canon_db)
    connection.row_factory = sqlite3.Row
    return connection


def test_meta_counts(canon_db: Path):
    with connect(canon_db) as connection:
        meta = {row["key"]: row["value"] for row in connection.execute("SELECT key, value FROM meta")}

    for key, expected in EXPECTED.items():
        assert int(meta[key]) == expected, key
    assert meta["schema_version"] == "1"
    assert meta["source_snapshot_date"] == "2026-09-09"


def test_every_player_has_ratings_and_22_stats(canon_db: Path):
    with connect(canon_db) as connection:
        rows = connection.execute("SELECT id, overall, pot, stats FROM players").fetchall()

    assert len(rows) == EXPECTED["players"]
    for row in rows:
        assert row["overall"] is not None, row["id"]
        assert 0 < row["overall"] <= 99, row["id"]
        assert row["pot"] is not None, row["id"]
        stats = json.loads(row["stats"])
        assert len(stats) == 22, row["id"]
        assert all(0 <= value <= 99 for value in stats.values()), row["id"]


def test_free_agents_receive_citizenship_and_value(canon_db: Path):
    with connect(canon_db) as connection:
        rows = connection.execute(
            "SELECT id, citizenship, market_value FROM players WHERE club_id IS NULL"
        ).fetchall()

    assert len(rows) == EXPECTED["free_agents"]
    for row in rows:
        assert json.loads(row["citizenship"]), row["id"]
        assert row["market_value"] > 0, row["id"]


def test_clubs_link_to_league_and_country(canon_db: Path):
    with connect(canon_db) as connection:
        orphaned = connection.execute(
            """
            SELECT COUNT(*) FROM clubs c
            LEFT JOIN leagues l ON l.id = c.league_id
            LEFT JOIN countries co ON co.id = c.country_id
            WHERE l.id IS NULL OR co.id IS NULL OR l.country_id != c.country_id
            """
        ).fetchone()[0]
        stats = connection.execute(
            "SELECT COUNT(*) FROM leagues WHERE tier_rank BETWEEN 1 AND 8"
        ).fetchone()[0]

    assert orphaned == 0
    assert stats == EXPECTED["leagues"]
