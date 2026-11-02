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
    player_contracts: dict[str, dict] = field(default_factory=dict)
    player_values: dict[str, int] = field(default_factory=dict)
    player_ages: dict[str, int] = field(default_factory=dict)
    player_transfers: dict[str, str] = field(default_factory=dict)
    shirt_numbers: dict[str, int] = field(default_factory=dict)
    negotiations: dict[str, dict] = field(default_factory=dict)
    transfer_offers: list[dict] = field(default_factory=list)
    transfer_contracts: dict[str, dict] = field(default_factory=dict)
    pending_transfers: list[dict] = field(default_factory=list)
    shortlist: list[str] = field(default_factory=list)
    scouts: list[dict] = field(default_factory=list)
    scout_assignments: dict[str, dict] = field(default_factory=dict)
    scout_tasks: dict[str, dict] = field(default_factory=dict)
    scout_reports: dict[str, dict] = field(default_factory=dict)
    scout_found: dict[str, dict] = field(default_factory=dict)
    scout_networks: list[dict] = field(default_factory=list)
    balance: int | None = None
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
                    "stats_by_competition": {
                        competition_id: dict(block)
                        for competition_id, block in (
                            state.get("stats_by_competition") or {}
                        ).items()
                    },
                }
                for player_id, state in self.player_state.items()
            }
        if self.player_contracts:
            payload["player_contracts"] = {
                player_id: dict(contract)
                for player_id, contract in self.player_contracts.items()
            }
        if self.player_values:
            payload["player_values"] = {
                player_id: int(value) for player_id, value in self.player_values.items()
            }
        if self.player_ages:
            payload["player_ages"] = {
                player_id: int(age) for player_id, age in self.player_ages.items()
            }
        if self.player_transfers:
            payload["player_transfers"] = {
                player_id: str(status)
                for player_id, status in self.player_transfers.items()
            }
        if self.shirt_numbers:
            payload["shirt_numbers"] = {
                player_id: int(number) for player_id, number in self.shirt_numbers.items()
            }
        if self.transfer_offers:
            payload["transfer_offers"] = [
                {
                    **offer,
                    "counter": None
                    if offer.get("counter") is None
                    else dict(offer["counter"]),
                    "demand": dict(offer.get("demand") or {}),
                }
                for offer in self.transfer_offers
            ]
        if self.shortlist:
            payload["shortlist"] = list(self.shortlist)
        if self.transfer_contracts:
            payload["transfer_contracts"] = {
                player_id: {
                    **state,
                    "demand": dict(state.get("demand") or {}),
                    "offer": None if state.get("offer") is None else dict(state["offer"]),
                    "counter": None
                    if state.get("counter") is None
                    else dict(state["counter"]),
                    "agreed": None
                    if state.get("agreed") is None
                    else dict(state["agreed"]),
                }
                for player_id, state in self.transfer_contracts.items()
            }
        if self.pending_transfers:
            payload["pending_transfers"] = [
                {**item, "terms": dict(item.get("terms") or {})}
                for item in self.pending_transfers
            ]
        if self.negotiations:
            payload["negotiations"] = {
                player_id: {
                    **state,
                    "demand": dict(state.get("demand") or {}),
                    "offer": None if state.get("offer") is None else dict(state["offer"]),
                    "counter": None
                    if state.get("counter") is None
                    else dict(state["counter"]),
                }
                for player_id, state in self.negotiations.items()
            }
        if self.scouts:
            payload["scouts"] = [dict(scout) for scout in self.scouts]
        if self.scout_assignments:
            payload["scout_assignments"] = {
                scout_id: dict(report)
                for scout_id, report in self.scout_assignments.items()
            }
        if self.scout_tasks:
            payload["scout_tasks"] = {
                scout_id: {
                    **task,
                    "criteria": dict(task.get("criteria") or {}),
                    "found": list(task.get("found") or []),
                }
                for scout_id, task in self.scout_tasks.items()
            }
        if self.scout_reports:
            payload["scout_reports"] = {
                player_id: dict(report)
                for player_id, report in self.scout_reports.items()
            }
        if self.scout_found:
            payload["scout_found"] = {
                player_id: dict(entry) for player_id, entry in self.scout_found.items()
            }
        if self.scout_networks:
            payload["scout_networks"] = [
                dict(network) for network in self.scout_networks
            ]
        if self.balance is not None:
            payload["balance"] = int(self.balance)
        if self.condition_date is not None:
            payload["condition_date"] = self.condition_date
        return payload

    @classmethod
    def from_save(cls, raw: dict) -> Career:
        lineup = raw.get("lineup")
        bench = raw.get("bench")
        schedule = raw.get("schedule")
        transfer_offers = []
        seen_offer_players = set()
        for offer in reversed(raw.get("transfer_offers") or []):
            if not isinstance(offer, dict):
                continue
            player_id = str(offer.get("player_id") or "")
            if player_id in seen_offer_players:
                continue
            seen_offer_players.add(player_id)
            transfer_offers.append(
                {
                    **offer,
                    "counter": None
                    if offer.get("counter") is None
                    else dict(offer["counter"]),
                    "demand": dict(offer.get("demand") or {}),
                }
            )
        transfer_offers.reverse()
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
            player_contracts={
                str(player_id): dict(contract)
                for player_id, contract in (raw.get("player_contracts") or {}).items()
                if isinstance(contract, dict)
            },
            player_values={
                str(player_id): int(value)
                for player_id, value in (raw.get("player_values") or {}).items()
            },
            player_ages={
                str(player_id): int(age)
                for player_id, age in (raw.get("player_ages") or {}).items()
            },
            player_transfers={
                str(player_id): str(status)
                for player_id, status in (raw.get("player_transfers") or {}).items()
                if status
            },
            shirt_numbers={
                str(player_id): int(number)
                for player_id, number in (raw.get("shirt_numbers") or {}).items()
            },
            negotiations={
                str(player_id): {
                    **state,
                    "demand": dict(state.get("demand") or {}),
                    "offer": None
                    if state.get("offer") is None
                    else dict(state["offer"]),
                    "counter": None
                    if state.get("counter") is None
                    else dict(state["counter"]),
                }
                for player_id, state in (raw.get("negotiations") or {}).items()
                if isinstance(state, dict)
            },
            transfer_contracts={
                str(player_id): {
                    **state,
                    "demand": dict(state.get("demand") or {}),
                    "offer": None
                    if state.get("offer") is None
                    else dict(state["offer"]),
                    "counter": None
                    if state.get("counter") is None
                    else dict(state["counter"]),
                    "agreed": None
                    if state.get("agreed") is None
                    else dict(state["agreed"]),
                }
                for player_id, state in (raw.get("transfer_contracts") or {}).items()
                if isinstance(state, dict)
            },
            pending_transfers=[
                {
                    **item,
                    "terms": dict(item.get("terms") or {}),
                }
                for item in (raw.get("pending_transfers") or [])
                if isinstance(item, dict)
            ],
            shortlist=[
                str(player_id) for player_id in (raw.get("shortlist") or [])
            ],
            transfer_offers=transfer_offers,
            scouts=[
                dict(scout)
                for scout in (raw.get("scouts") or [])
                if isinstance(scout, dict)
            ],
            scout_assignments={
                str(scout_id): dict(report)
                for scout_id, report in (raw.get("scout_assignments") or {}).items()
                if isinstance(report, dict)
            },
            scout_tasks={
                str(scout_id): {
                    **task,
                    "criteria": dict(task.get("criteria") or {}),
                    "found": list(task.get("found") or []),
                }
                for scout_id, task in (raw.get("scout_tasks") or {}).items()
                if isinstance(task, dict)
            },
            scout_reports={
                str(player_id): dict(report)
                for player_id, report in (raw.get("scout_reports") or {}).items()
                if isinstance(report, dict)
            },
            scout_found={
                str(player_id): dict(entry)
                for player_id, entry in (raw.get("scout_found") or {}).items()
                if isinstance(entry, dict)
            },
            scout_networks=[
                dict(network)
                for network in (raw.get("scout_networks") or [])
                if isinstance(network, dict)
            ],
            balance=None if raw.get("balance") is None else int(raw["balance"]),
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
