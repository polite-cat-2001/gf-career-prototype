from __future__ import annotations

import json
import os
import sqlite3
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = REPO_ROOT / "canon.db"
CUTOUT_FACES_DIR = REPO_ROOT / "data" / "raster" / "players_faces_cutout"


def _cutout_face_ids() -> frozenset[str]:
    if not CUTOUT_FACES_DIR.is_dir():
        return frozenset()
    return frozenset(path.stem for path in CUTOUT_FACES_DIR.iterdir() if path.suffix == ".png")


CUTOUT_FACE_IDS = _cutout_face_ids()

COUNTRY_COLUMNS = "co.id, co.name, co.flag"
LEAGUE_COLUMNS = "l.id, l.name, l.country_id, l.tier, l.tier_rank, l.logo"
CLUB_COLUMNS = (
    "c.id, c.name, c.league_id, c.country_id, c.logo, c.colors, "
    "c.stadium_name, c.stadium_seats, c.founded_on"
)
PLAYER_COLUMNS = (
    "p.id, p.name, p.first_name, p.last_name, p.birth_date, p.height, p.foot, "
    "p.citizenship, p.position, p.position_other, p.club_id, p.national_team_id, "
    "p.shirt_number, p.market_value, p.overall, p.pot, p.weight, p.weak_foot, "
    "p.skill_moves, p.role, p.stats"
)

ROLE_ORDER = {
    "GK": 0,
    "CB": 1,
    "LB": 2,
    "RB": 3,
    "DM": 4,
    "CM": 5,
    "LM": 6,
    "RM": 7,
    "AM": 8,
    "CF": 9,
}


def default_db_path() -> Path:
    return Path(os.environ.get("GF_CANON_DB", DEFAULT_DB))


def age_from_birth_date(birth_date: str | None) -> int | None:
    if not birth_date:
        return None
    try:
        born = date.fromisoformat(birth_date)
    except ValueError:
        return None
    today = date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


def _json_list(value: str | None) -> list:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


class Canon:
    def __init__(self, path: Path | None = None):
        self.path = Path(path or default_db_path())
        if not self.path.exists():
            raise FileNotFoundError(
                f"canon.db not found at {self.path}; run `python scripts/build_canon_db.py`"
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(f"file:{self.path.as_posix()}?mode=ro", uri=True)
        connection.row_factory = sqlite3.Row
        return connection

    def meta(self) -> dict:
        with self._connect() as connection:
            rows = connection.execute("SELECT key, value FROM meta").fetchall()
        raw = {row["key"]: row["value"] for row in rows}
        integer_keys = {
            "countries",
            "leagues",
            "clubs",
            "players",
            "national_teams",
            "stats_per_player",
            "free_agents",
            "free_agents_enriched",
        }
        counts = {key: int(raw[key]) for key in integer_keys if key in raw}
        return {
            "schema_version": int(raw.get("schema_version", 0)),
            "source_snapshot_date": raw.get("source_snapshot_date"),
            "counts": counts,
        }

    def countries(self) -> list[dict]:
        query = f"""
            SELECT {COUNTRY_COLUMNS},
                (SELECT COUNT(*) FROM leagues l WHERE l.country_id = co.id) AS leagues_count,
                (SELECT COUNT(*) FROM clubs c WHERE c.country_id = co.id) AS clubs_count
            FROM countries co
            ORDER BY co.name
        """
        with self._connect() as connection:
            rows = connection.execute(query).fetchall()
        return [dict(row) for row in rows]

    def leagues(self, country_id: str | None = None) -> list[dict]:
        query = f"""
            SELECT {LEAGUE_COLUMNS}, co.name AS country_name, co.flag AS country_flag,
                (SELECT COUNT(*) FROM clubs c WHERE c.league_id = l.id) AS clubs_count
            FROM leagues l
            JOIN countries co ON co.id = l.country_id
            WHERE (? IS NULL OR l.country_id = ?)
            ORDER BY co.name, l.tier_rank, l.name
        """
        with self._connect() as connection:
            rows = connection.execute(query, (country_id, country_id)).fetchall()
        return [dict(row) for row in rows]

    def clubs(
        self,
        league_id: str | None = None,
        country_id: str | None = None,
        limit: int = 500,
        offset: int = 0,
    ) -> list[dict]:
        query = f"""
            SELECT {CLUB_COLUMNS}, l.name AS league_name, l.tier, l.tier_rank,
                co.name AS country_name, co.flag AS country_flag
            FROM clubs c
            JOIN leagues l ON l.id = c.league_id
            JOIN countries co ON co.id = c.country_id
            WHERE (? IS NULL OR c.league_id = ?)
              AND (? IS NULL OR c.country_id = ?)
            ORDER BY co.name, l.tier_rank, l.name, c.name
            LIMIT ? OFFSET ?
        """
        with self._connect() as connection:
            rows = connection.execute(
                query, (league_id, league_id, country_id, country_id, limit, offset)
            ).fetchall()
        return [self._club_row(row) for row in rows]

    def club(self, club_id: str) -> dict | None:
        query = f"""
            SELECT {CLUB_COLUMNS}, l.name AS league_name, l.tier, l.tier_rank,
                co.name AS country_name, co.flag AS country_flag
            FROM clubs c
            JOIN leagues l ON l.id = c.league_id
            JOIN countries co ON co.id = c.country_id
            WHERE c.id = ?
        """
        with self._connect() as connection:
            row = connection.execute(query, (club_id,)).fetchone()
        return self._club_row(row) if row else None

    def squad(self, club_id: str) -> list[dict]:
        rows = self._player_rows("WHERE p.club_id = ?", (club_id,))
        for player in rows:
            player.pop("stats", None)
        rows.sort(key=lambda player: (ROLE_ORDER.get(player["role"], 99), -player["overall"], player["name"]))
        return rows

    def player(self, player_id: str) -> dict | None:
        rows = self._player_rows("WHERE p.id = ?", (player_id,))
        if not rows:
            return None
        player = rows[0]
        player["stats"] = json.loads(player.pop("stats"))
        return player

    def _player_rows(self, where: str, params: tuple) -> list[dict]:
        query = f"SELECT {PLAYER_COLUMNS} FROM players p {where}"
        with self._connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [self._player_row(row) for row in rows]

    @staticmethod
    def _club_row(row: sqlite3.Row) -> dict:
        return {
            "id": row["id"],
            "name": row["name"],
            "league_id": row["league_id"],
            "league_name": row["league_name"],
            "tier": row["tier"],
            "tier_rank": row["tier_rank"],
            "country_id": row["country_id"],
            "country_name": row["country_name"],
            "country_flag": row["country_flag"],
            "logo": row["logo"],
            "colors": _json_list(row["colors"]),
            "stadium": {"name": row["stadium_name"], "seats": row["stadium_seats"]},
            "founded_on": row["founded_on"],
        }

    @staticmethod
    def _player_row(row: sqlite3.Row) -> dict:
        if row["id"] in CUTOUT_FACE_IDS:
            photo = f"/raster/players_faces_cutout/{row['id']}.png"
        else:
            photo = f"/raster/players_faces/{row['id']}.jpg"
        return {
            "id": row["id"],
            "name": row["name"],
            "first_name": row["first_name"],
            "last_name": row["last_name"],
            "birth_date": row["birth_date"],
            "age": age_from_birth_date(row["birth_date"]),
            "height": row["height"],
            "foot": row["foot"],
            "citizenship": _json_list(row["citizenship"]),
            "position": row["position"],
            "position_other": _json_list(row["position_other"]),
            "club_id": row["club_id"],
            "national_team_id": row["national_team_id"],
            "shirt_number": row["shirt_number"],
            "market_value": row["market_value"],
            "overall": round(row["overall"], 1),
            "pot": row["pot"],
            "weight": row["weight"],
            "weak_foot": row["weak_foot"],
            "skill_moves": row["skill_moves"],
            "role": row["role"],
            "stats": row["stats"],
            "photo": photo,
        }
