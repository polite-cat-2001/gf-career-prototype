from __future__ import annotations

import secrets
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

SAVE_VERSION = 1
START_DATE = "2026-07-01"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def new_seed() -> int:
    return secrets.randbits(32)


@dataclass
class Manager:
    name: str
    nationality_id: str
    nationality: str

    def to_save(self) -> dict:
        return {
            "name": self.name,
            "nationality_id": self.nationality_id,
            "nationality": self.nationality,
        }

    @classmethod
    def from_save(cls, raw: dict) -> Manager:
        return cls(
            name=str(raw["name"]),
            nationality_id=str(raw["nationality_id"]),
            nationality=str(raw["nationality"]),
        )


@dataclass
class Career:
    id: str
    seed: int
    manager: Manager
    club_id: str
    player_ids: list[str]
    league_id: str | None = None
    league_club_ids: list[str] | None = None
    date: str = START_DATE
    season_start: str = START_DATE
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    lineup: list[str] | None = None
    bench_order: list[str] | None = None
    schedule: list[dict] | None = None
    schedule_version: int = 0
    results: dict[str, dict] = field(default_factory=dict)
    player_state: dict[str, dict] = field(default_factory=dict)
    condition_date: str | None = None
    journal: list[dict] = field(default_factory=list)
    version: int = SAVE_VERSION

    def touch(self) -> None:
        self.updated_at = utc_now()

    def to_save(self) -> dict:
        payload = {
            "version": self.version,
            "id": self.id,
            "seed": self.seed,
            "date": self.date,
            "season_start": self.season_start,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "manager": self.manager.to_save(),
            "club_id": self.club_id,
            "player_ids": list(self.player_ids),
            "journal": list(self.journal),
        }
        if self.league_id is not None:
            payload["league_id"] = self.league_id
        if self.league_club_ids is not None:
            payload["league_club_ids"] = list(self.league_club_ids)
        if self.lineup is not None:
            payload["lineup"] = list(self.lineup)
        if self.bench_order is not None:
            payload["bench"] = list(self.bench_order)
        if self.schedule is not None:
            payload["schedule"] = list(self.schedule)
            payload["schedule_version"] = self.schedule_version
        if self.results:
            payload["results"] = dict(self.results)
        if self.player_state:
            payload["player_state"] = {
                player_id: {
                    **state,
                    "stats": dict(state.get("stats") or {}),
                }
                for player_id, state in self.player_state.items()
            }
        if self.condition_date is not None:
            payload["condition_date"] = self.condition_date
        return payload

    @classmethod
    def from_save(cls, raw: dict) -> Career:
        lineup = raw.get("lineup")
        bench = raw.get("bench")
        schedule = raw.get("schedule")
        return cls(
            version=int(raw["version"]),
            id=str(raw["id"]),
            seed=int(raw["seed"]),
            date=str(raw["date"]),
            season_start=str(raw.get("season_start") or START_DATE),
            created_at=str(raw["created_at"]),
            updated_at=str(raw["updated_at"]),
            manager=Manager.from_save(raw["manager"]),
            club_id=str(raw["club_id"]),
            player_ids=[str(player_id) for player_id in raw["player_ids"]],
            league_id=None if raw.get("league_id") is None else str(raw["league_id"]),
            league_club_ids=None
            if raw.get("league_club_ids") is None
            else [str(club_id) for club_id in raw["league_club_ids"]],
            lineup=None if lineup is None else [str(player_id) for player_id in lineup],
            bench_order=None if bench is None else [str(player_id) for player_id in bench],
            schedule=None
            if schedule is None
            else [
                {
                    "id": str(fixture["id"]),
                    "round": int(fixture["round"]),
                    "date": str(fixture["date"]),
                    "home": str(fixture["home"]),
                    "away": str(fixture["away"]),
                }
                for fixture in schedule
            ],
            schedule_version=int(raw.get("schedule_version") or 0),
            results={
                str(fixture_id): {
                    "home": int(score["home"]),
                    "away": int(score["away"]),
                }
                for fixture_id, score in (raw.get("results") or {}).items()
            },
            player_state={
                str(player_id): dict(state)
                for player_id, state in (raw.get("player_state") or {}).items()
                if isinstance(state, dict)
            },
            condition_date=raw.get("condition_date"),
            journal=list(raw.get("journal", [])),
        )


def create_career(
    *,
    manager_name: str,
    manager_nationality_id: str,
    manager_nationality: str,
    club_id: str,
    player_ids: list[str],
    seed: int | None = None,
) -> Career:
    return Career(
        id=uuid.uuid4().hex,
        seed=new_seed() if seed is None else seed,
        manager=Manager(
            name=manager_name,
            nationality_id=manager_nationality_id,
            nationality=manager_nationality,
        ),
        club_id=club_id,
        player_ids=list(player_ids),
    )
