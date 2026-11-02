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


def age_from_birth_date(birth_date: str | None, ref_date: str | None = None) -> int | None:
    if not birth_date:
        return None
    try:
        born = date.fromisoformat(birth_date)
        ref = date.fromisoformat(ref_date) if ref_date else date.today()
    except ValueError:
        return None
    return ref.year - born.year - ((ref.month, ref.day) < (born.month, born.day))


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

    def country(self, country_id: str) -> dict | None:
        query = f"SELECT {COUNTRY_COLUMNS} FROM countries co WHERE co.id = ?"
        with self._connect() as connection:
            row = connection.execute(query, (country_id,)).fetchone()
        return dict(row) if row else None

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

    def squads_for_clubs(self, club_ids: list[str]) -> dict[str, list[dict]]:
        if not club_ids:
            return {}
        placeholders = ",".join("?" for _ in club_ids)
        rows = self._player_rows(
            f"WHERE p.club_id IN ({placeholders})", tuple(str(club_id) for club_id in club_ids)
        )
        result: dict[str, list[dict]] = {str(club_id): [] for club_id in club_ids}
        for player in rows:
            player.pop("stats", None)
            result.setdefault(str(player["club_id"]), []).append(player)
        for players in result.values():
            players.sort(
                key=lambda player: (
                    ROLE_ORDER.get(player["role"], 99),
                    -float(player["overall"] or 0),
                    player["name"],
                )
            )
        return result

    def free_agents(self, limit: int = 2000, offset: int = 0) -> list[dict]:
        rows = self._player_rows(
            "WHERE p.club_id IS NULL ORDER BY p.id LIMIT ? OFFSET ?",
            (limit, offset),
        )
        for player in rows:
            player.pop("stats", None)
        return rows

    def club_role_stats(self) -> dict[str, dict[str, dict]]:
        query = """
            SELECT club_id, role, COUNT(*) AS count, MAX(overall) AS best
            FROM players
            WHERE club_id IS NOT NULL
            GROUP BY club_id, role
        """
        with self._connect() as connection:
            rows = connection.execute(query).fetchall()
        result: dict[str, dict[str, dict]] = {}
        for row in rows:
            result.setdefault(str(row["club_id"]), {})[str(row["role"])] = {
                "count": int(row["count"]),
                "best": float(row["best"] or 0),
            }
        return result

    def players_by_ids(self, player_ids: list[str], with_stats: bool = False) -> list[dict]:
        if not player_ids:
            return []
        placeholders = ",".join("?" for _ in player_ids)
        rows = self._player_rows(f"WHERE p.id IN ({placeholders})", tuple(player_ids))
        by_id = {row["id"]: row for row in rows}
        players = [by_id[player_id] for player_id in player_ids if player_id in by_id]
        for player in players:
            if with_stats:
                player["stats"] = json.loads(player["stats"])
            else:
                player.pop("stats", None)
        return players

    def player(self, player_id: str) -> dict | None:
        rows = self._player_rows("WHERE p.id = ?", (player_id,))
        if not rows:
            return None
        player = rows[0]
        player["stats"] = json.loads(player.pop("stats"))
        return player

    def search_players(
        self,
        *,
        name: str | None = None,
        group: str | None = None,
        position: str | None = None,
        age_min: int | None = None,
        age_max: int | None = None,
        citizenship: str | None = None,
        country_id: str | None = None,
        league_id: str | None = None,
        club_id: str | None = None,
        foot: str | None = None,
        height_min: int | None = None,
        height_max: int | None = None,
        free_only: bool = False,
        only_ids: list[str] | None = None,
        sort: str = "name",
        direction: str = "asc",
        limit: int = 50,
        offset: int = 0,
        ref_date: str | None = None,
    ) -> tuple[list[dict], int]:
        if only_ids is not None and not only_ids:
            return [], 0
        reference = ref_date or date.today().isoformat()
        age_sql = f"CAST((julianday(?) - julianday(p.birth_date)) / 365.2425 AS INTEGER)"
        conditions = ["1 = 1"]
        params: list = []
        if name:
            conditions.append("p.name LIKE ? COLLATE NOCASE")
            params.append(f"%{name}%")
        if group:
            roles = {
                "GK": ("GK",),
                "DEF": ("CB", "LB", "RB"),
                "MID": ("DM", "CM", "LM", "RM", "AM"),
                "FWD": ("CF",),
            }.get(group.upper())
            if roles:
                placeholders = ",".join("?" for _ in roles)
                conditions.append(f"p.role IN ({placeholders})")
                params.extend(roles)
            else:
                conditions.append("1 = 0")
        if position:
            conditions.append("(p.position = ? OR p.position_other LIKE ?)")
            params.extend([position, f'%"{position}"%'])
        if age_min is not None:
            conditions.append(f"{age_sql} >= ?")
            params.extend([reference, age_min])
        if age_max is not None:
            conditions.append(f"{age_sql} <= ?")
            params.extend([reference, age_max])
        if citizenship:
            conditions.append("p.citizenship LIKE ?")
            params.append(f'%"{citizenship}"%')
        if country_id:
            conditions.append("c.country_id = ?")
            params.append(country_id)
        if league_id:
            conditions.append("c.league_id = ?")
            params.append(league_id)
        if club_id:
            conditions.append("p.club_id = ?")
            params.append(club_id)
        if foot:
            conditions.append("p.foot = ?")
            params.append(foot)
        if height_min is not None:
            conditions.append("p.height >= ?")
            params.append(height_min)
        if height_max is not None:
            conditions.append("p.height <= ?")
            params.append(height_max)
        if free_only:
            conditions.append("p.club_id IS NULL")
        if only_ids is not None:
            placeholders = ",".join("?" for _ in only_ids)
            conditions.append(f"p.id IN ({placeholders})")
            params.extend(only_ids)
        where_sql = " AND ".join(conditions)
        base_from = """
            FROM players p
            LEFT JOIN clubs c ON c.id = p.club_id
            LEFT JOIN leagues l ON l.id = c.league_id
            LEFT JOIN countries co ON co.id = c.country_id
        """
        sort_sql = {
            "name": "p.name COLLATE NOCASE",
            "age": age_sql,
            "overall": "p.overall",
            "position": (
                "CASE p.role WHEN 'GK' THEN 0 WHEN 'CB' THEN 1 WHEN 'LB' THEN 2 "
                "WHEN 'RB' THEN 3 WHEN 'DM' THEN 4 WHEN 'CM' THEN 5 WHEN 'LM' THEN 6 "
                "WHEN 'RM' THEN 7 WHEN 'AM' THEN 8 WHEN 'CF' THEN 9 ELSE 99 END"
            ),
            "value": "p.market_value",
            "wage": (
                "p.market_value * CASE WHEN p.birth_date IS NULL THEN 1.0 "
                "WHEN " + age_sql + " <= 23 THEN 1.1 WHEN " + age_sql + " <= 28 THEN 1.0 "
                "WHEN " + age_sql + " <= 31 THEN 0.9 ELSE 0.8 END"
            ),
        }
        order_expr = sort_sql.get(sort, sort_sql["name"])
        order_dir = "DESC" if direction == "desc" else "ASC"
        order_params: list = []
        if order_expr == age_sql:
            order_params.append(reference)
        elif sort == "wage":
            order_params.extend([reference, reference, reference])
        columns = """
            p.id, p.name, p.first_name, p.last_name, p.birth_date, p.height, p.foot,
            p.citizenship, p.position, p.position_other, p.club_id, p.national_team_id,
            p.shirt_number, p.market_value, p.overall, p.pot, p.weight, p.weak_foot,
            p.skill_moves, p.role, p.stats,
            c.name AS club_name, c.logo AS club_logo, c.league_id AS league_id,
            l.name AS league_name, c.country_id AS country_id, co.name AS country_name
        """
        count_query = f"SELECT COUNT(*) AS total {base_from} WHERE {where_sql}"
        query = (
            f"SELECT {columns} {base_from} WHERE {where_sql} "
            f"ORDER BY {order_expr} {order_dir} NULLS LAST, p.name COLLATE NOCASE "
            "LIMIT ? OFFSET ?"
        )
        with self._connect() as connection:
            total = connection.execute(count_query, tuple(params)).fetchone()["total"]
            rows = connection.execute(
                query, tuple(params) + tuple(order_params) + (limit, offset)
            ).fetchall()
        return [self._transfer_row(row, reference) for row in rows], int(total)

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
    def _face_path(player_id: str) -> str:
        if player_id in CUTOUT_FACE_IDS:
            return f"/raster/players_faces_cutout/{player_id}.png"
        return f"/raster/players_faces/{player_id}.jpg"

    @staticmethod
    def _transfer_row(row: sqlite3.Row, reference: str) -> dict:
        return {
            "id": row["id"],
            "name": row["name"],
            "first_name": row["first_name"],
            "last_name": row["last_name"],
            "birth_date": row["birth_date"],
            "age": age_from_birth_date(row["birth_date"], reference),
            "height": row["height"],
            "foot": row["foot"],
            "citizenship": _json_list(row["citizenship"]),
            "position": row["position"],
            "position_other": _json_list(row["position_other"]),
            "club_id": row["club_id"],
            "club_name": row["club_name"],
            "club_logo": row["club_logo"],
            "league_id": row["league_id"],
            "league_name": row["league_name"],
            "country_id": row["country_id"],
            "country_name": row["country_name"],
            "national_team_id": row["national_team_id"],
            "shirt_number": row["shirt_number"],
            "market_value": row["market_value"],
            "overall": round(row["overall"], 1),
            "pot": row["pot"],
            "weight": row["weight"],
            "weak_foot": row["weak_foot"],
            "skill_moves": row["skill_moves"],
            "role": row["role"],
            "stats": json.loads(row["stats"]) if row["stats"] else None,
            "photo": Canon._face_path(row["id"]),
        }

    @staticmethod
    def _player_row(row: sqlite3.Row) -> dict:
        photo = Canon._face_path(row["id"])
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
