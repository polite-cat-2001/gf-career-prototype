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
    date: str = START_DATE
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    journal: list[dict] = field(default_factory=list)
    version: int = SAVE_VERSION

    def touch(self) -> None:
        self.updated_at = utc_now()

    def to_save(self) -> dict:
        return {
            "version": self.version,
            "id": self.id,
            "seed": self.seed,
            "date": self.date,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "manager": self.manager.to_save(),
            "club_id": self.club_id,
            "player_ids": list(self.player_ids),
            "journal": list(self.journal),
        }

    @classmethod
    def from_save(cls, raw: dict) -> Career:
        return cls(
            version=int(raw["version"]),
            id=str(raw["id"]),
            seed=int(raw["seed"]),
            date=str(raw["date"]),
            created_at=str(raw["created_at"]),
            updated_at=str(raw["updated_at"]),
            manager=Manager.from_save(raw["manager"]),
            club_id=str(raw["club_id"]),
            player_ids=[str(player_id) for player_id in raw["player_ids"]],
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
