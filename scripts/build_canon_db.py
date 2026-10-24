"""Build the read-only canon database from transfermarkt JSON and ratings."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_JSON_DIR = REPO_ROOT / "data" / "json"
DEFAULT_OUT = REPO_ROOT / "canon.db"

TIER_NAMES = {
    "First Tier": 1,
    "Second Tier": 2,
    "Third Tier": 3,
    "Fourth Tier": 4,
    "Fifth Tier": 5,
    "Sixth Tier": 6,
    "Reserve league": 7,
    "Youth league": 8,
}

SCHEMA = """
CREATE TABLE meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE countries (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    flag TEXT NOT NULL
);

CREATE TABLE leagues (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    country_id TEXT NOT NULL REFERENCES countries(id),
    tier TEXT NOT NULL,
    tier_rank INTEGER NOT NULL,
    logo TEXT NOT NULL
);

CREATE TABLE clubs (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    league_id TEXT NOT NULL REFERENCES leagues(id),
    country_id TEXT NOT NULL REFERENCES countries(id),
    logo TEXT NOT NULL,
    colors TEXT NOT NULL,
    stadium_name TEXT,
    stadium_seats INTEGER,
    founded_on TEXT
);

CREATE TABLE players (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    first_name TEXT,
    last_name TEXT,
    birth_date TEXT,
    height INTEGER,
    foot TEXT,
    citizenship TEXT NOT NULL,
    position TEXT NOT NULL,
    position_other TEXT NOT NULL,
    club_id TEXT REFERENCES clubs(id),
    national_team_id TEXT,
    shirt_number INTEGER,
    market_value INTEGER NOT NULL,
    overall REAL NOT NULL,
    pot INTEGER NOT NULL,
    weight INTEGER,
    weak_foot INTEGER,
    skill_moves INTEGER,
    role TEXT,
    stats TEXT NOT NULL
);

CREATE TABLE national_teams (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    flag TEXT NOT NULL
);

CREATE INDEX idx_clubs_league ON clubs(league_id);
CREATE INDEX idx_clubs_country ON clubs(country_id);
CREATE INDEX idx_leagues_country ON leagues(country_id);
CREATE INDEX idx_players_club ON players(club_id);
CREATE INDEX idx_players_overall ON players(overall DESC);
"""


def find_ratings_path(explicit: Path | None) -> Path:
    if explicit is not None:
        if not explicit.exists():
            raise FileNotFoundError(f"ratings file not found: {explicit}")
        return explicit

    candidates = [
        REPO_ROOT / "ratings_output.json",
        REPO_ROOT / "data" / "json" / "ratings_output.json",
        REPO_ROOT.parent / "ratings-generator" / "output.json",
        REPO_ROOT.parent / "ratings_output.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        "ratings_output.json not found; pass --ratings PATH "
        f"(looked in: {', '.join(str(c) for c in candidates)})"
    )


def load_json(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def flag_path(kind: str, item_id: str, ext: str = "png") -> str:
    return f"/raster/{kind}/{item_id}.{ext}"


def optional_int(value):
    if value in (None, "", "-"):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def build_canon_db(
    json_dir: Path = DEFAULT_JSON_DIR,
    ratings_path: Path | None = None,
    out_path: Path = DEFAULT_OUT,
) -> dict[str, int]:
    started = time.perf_counter()
    json_dir = Path(json_dir)
    out_path = Path(out_path)
    ratings_path = find_ratings_path(ratings_path)

    ratings = load_json(ratings_path)
    players = load_json(json_dir / "players.json")
    clubs = load_json(json_dir / "clubs.json")
    competitions = load_json(json_dir / "competitions.json")
    national_teams = load_json(json_dir / "national_teams.json")
    snapshot = load_json(json_dir / "meta.json")

    tmp_path = out_path.with_name(out_path.name + ".tmp")
    if tmp_path.exists():
        tmp_path.unlink()

    country_rows: dict[str, tuple[str, str, str]] = {}
    league_rows: list[tuple] = []
    league_country: dict[str, str] = {}

    for competition in competitions:
        country = competition.get("country") or {}
        country_id = str(country.get("id") or "")
        if not country_id:
            continue
        country_rows.setdefault(
            country_id,
            (country_id, country.get("name") or country_id, flag_path("country_flags", country_id)),
        )
        league_id = str(competition["id"])
        tier = competition.get("tier") or "First Tier"
        league_rows.append(
            (
                league_id,
                competition.get("name") or league_id,
                country_id,
                tier,
                TIER_NAMES.get(tier, 99),
                flag_path("leagues", league_id),
            )
        )
        league_country[league_id] = country_id

    league_rows.sort(key=lambda row: (row[2], row[4], row[1]))

    club_rows = []
    for club in clubs:
        league_id = str(club["league_id"])
        country_id = league_country[league_id]
        stadium = club.get("stadium") or {}
        club_rows.append(
            (
                str(club["id"]),
                club.get("name") or str(club["id"]),
                league_id,
                country_id,
                flag_path("teams_emblems", str(club["id"])),
                json.dumps(club.get("colors") or [], ensure_ascii=False),
                stadium.get("name"),
                stadium.get("seats"),
                club.get("founded_on"),
            )
        )
    club_rows.sort(key=lambda row: (row[3], row[2], row[1]))

    player_rows = []
    stat_names: set[str] | None = None
    missing_ratings: list[str] = []
    missing_citizenship = 0
    for player in players:
        player_id = str(player["id"])
        rating = ratings.get(player_id)
        if rating is None:
            missing_ratings.append(player_id)
            continue

        stats = rating.get("stats") or {}
        if stat_names is None:
            stat_names = set(stats)
        elif set(stats) != stat_names:
            raise ValueError(f"inconsistent stat set for player {player_id}")

        citizenship = [c for c in (player.get("citizenship") or []) if c]
        if not citizenship and rating.get("country"):
            citizenship = [rating["country"]]
            missing_citizenship += 1

        market_value = player.get("market_value") or 0
        if not player.get("club_id"):
            market_value = rating.get("adjusted_mv") or rating.get("market_value") or 0
        elif not market_value:
            market_value = rating.get("adjusted_mv") or rating.get("market_value") or 0

        position = player.get("position") or {}
        player_rows.append(
            (
                player_id,
                player.get("name") or rating.get("name") or player_id,
                player.get("first_name"),
                player.get("last_name"),
                player.get("birth_date"),
                optional_int(player.get("height") or rating.get("height")),
                player.get("foot") or rating.get("foot") or "",
                json.dumps(citizenship, ensure_ascii=False),
                position.get("main") or rating.get("position") or "",
                json.dumps(position.get("other") or [], ensure_ascii=False),
                str(player["club_id"]) if player.get("club_id") else None,
                str(player["national_team_id"]) if player.get("national_team_id") else None,
                optional_int(player.get("shirt_number")),
                int(market_value),
                float(rating["overall"]),
                int(rating["pot"]),
                rating.get("weight"),
                rating.get("weak_foot"),
                rating.get("skill_moves"),
                rating.get("role"),
                json.dumps(stats, ensure_ascii=False, sort_keys=True),
            )
        )

    if missing_ratings:
        raise ValueError(f"{len(missing_ratings)} players have no rating, e.g. {missing_ratings[:5]}")
    if stat_names is None or len(stat_names) != 22:
        raise ValueError(f"expected 22 stats, got {len(stat_names or [])}")

    national_team_rows = [
        (
            str(team["id"]),
            team.get("name") or str(team["id"]),
            flag_path("teams_flags", str(team["id"])),
        )
        for team in national_teams
    ]

    counts = {
        "countries": len(country_rows),
        "leagues": len(league_rows),
        "clubs": len(club_rows),
        "players": len(player_rows),
        "national_teams": len(national_team_rows),
        "stats_per_player": len(stat_names),
        "free_agents": sum(1 for row in player_rows if row[10] is None),
        "free_agents_enriched": missing_citizenship,
    }

    connection = sqlite3.connect(tmp_path)
    try:
        connection.executescript(SCHEMA)
        connection.executemany("INSERT INTO countries VALUES (?, ?, ?)", country_rows.values())
        connection.executemany("INSERT INTO leagues VALUES (?, ?, ?, ?, ?, ?)", league_rows)
        connection.executemany("INSERT INTO clubs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", club_rows)
        connection.executemany(
            "INSERT INTO players VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            player_rows,
        )
        connection.executemany("INSERT INTO national_teams VALUES (?, ?, ?)", national_team_rows)

        meta_rows = [
            ("schema_version", "1"),
            ("source_snapshot_date", str(snapshot.get("snapshot_date") or "")),
            ("ratings_source", str(ratings_path)),
        ]
        for key, value in counts.items():
            meta_rows.append((key, str(value)))
        connection.executemany("INSERT INTO meta VALUES (?, ?)", meta_rows)
        connection.commit()
    finally:
        connection.close()

    if out_path.exists():
        out_path.unlink()
    tmp_path.replace(out_path)

    counts["seconds"] = round(time.perf_counter() - started, 2)
    return counts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-dir", type=Path, default=DEFAULT_JSON_DIR)
    parser.add_argument("--ratings", type=Path, default=None, help="path to ratings_output.json")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)

    counts = build_canon_db(args.json_dir, args.ratings, args.out)
    summary = ", ".join(f"{key}={value}" for key, value in counts.items() if key != "seconds")
    print(f"Built {args.out} in {counts['seconds']}s: {summary}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
