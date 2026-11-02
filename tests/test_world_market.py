from __future__ import annotations

import json

from fastapi.testclient import TestClient

from server.career import create_career
from server.career.world_market import (
    MAX_BUYS,
    MAX_SELLS,
    SQUAD_MAX,
    SQUAD_MIN,
    advance_world_market,
    batch_schedule,
    batches_between,
    club_budget,
    effective_players,
    role_counts,
)

ENGLAND = "189"
ARSENAL = "11"


def make_clubs(count: int = 10) -> list[dict]:
    return [
        {
            "id": f"c{index}",
            "name": f"Club {index}",
            "country_id": ENGLAND,
        }
        for index in range(count)
    ]


def make_players(club_id: str, count: int = 20) -> list[dict]:
    return [
        {
            "id": f"{club_id}-p{index}",
            "name": f"{club_id} Player {index}",
            "role": ("GK", "CB", "CM", "CF")[index % 4],
            "overall": 60.0 + index,
            "market_value": 1_000_000 + index * 100_000,
            "club_id": club_id,
        }
        for index in range(count)
    ]


def make_world(clubs: list[dict], size: int = 20) -> dict[str, list[dict]]:
    return {str(club["id"]): make_players(str(club["id"]), size) for club in clubs}


def make_free_agents(count: int = 12) -> list[dict]:
    return [
        {
            "id": f"fa{index}",
            "name": f"Free Agent {index}",
            "role": ("GK", "CB", "CM", "CF")[index % 4],
            "overall": 62.0 + index,
            "market_value": 500_000,
            "club_id": None,
        }
        for index in range(count)
    ]


def make_career(seed: int = 99):
    return create_career(
        manager_name="World Tester",
        manager_nationality_id=ENGLAND,
        manager_nationality="England",
        club_id=ARSENAL,
        player_ids=["own"],
        seed=seed,
    )


def lookup_for(*groups: list[dict]):
    index = {str(player["id"]): player for group in groups for player in group}
    return lambda player_ids: [index[player_id] for player_id in player_ids if player_id in index]


def test_window_has_four_batches_with_non_overlapping_periods():
    batches = batch_schedule("2026-07-01", "2026-08-31")
    assert [batch["name"] for batch in batches] == [
        "opening",
        "middle",
        "last_week",
        "last_day",
    ]
    assert batches[0]["date"] == "2026-07-01"
    assert batches[-1]["date"] == "2026-08-31"
    assert batches[0]["period_start"] == "2026-07-01"
    assert batches[-1]["period_start"] == "2026-08-31"
    assert batches[-1]["period_end"] == "2026-08-31"
    for previous, current in zip(batches, batches[1:]):
        assert previous["period_end"] < current["period_start"]


def test_batches_between_only_returns_due_windows():
    assert batches_between("2026-06-30", "2026-06-30") == []
    due = batches_between("2026-06-30", "2026-07-01")
    assert [batch["name"] for batch in due] == ["opening"]
    assert [batch["name"] for batch in batches_between("2026-07-01", "2026-08-01")] == [
        "middle"
    ]
    assert batches_between("2026-09-01", "2026-12-31") == []


def test_market_keeps_clubs_within_limits_and_squad_bounds():
    clubs = make_clubs()
    squads = make_world(clubs)
    free_agents = make_free_agents()
    career = make_career()
    advance_world_market(
        career,
        clubs,
        squads,
        free_agents,
        previous_date="2026-06-30",
        target_date="2026-08-31",
        player_lookup=lookup_for(*squads.values(), free_agents),
    )

    assert career.world_transfers
    buys: dict[str, int] = {}
    sells: dict[str, int] = {}
    for transfer in career.world_transfers:
        buyer = transfer["to_club_id"]
        seller = transfer["from_club_id"]
        buys[buyer] = buys.get(buyer, 0) + 1
        if seller is not None:
            sells[seller] = sells.get(seller, 0) + 1
        assert "2026-07-01" <= transfer["date"] <= "2026-08-31"
        assert null_or_str(transfer["from_club_id"]) != transfer["to_club_id"]

    assert max(buys.values()) <= MAX_BUYS
    assert (max(sells.values()) if sells else 0) <= MAX_SELLS

    fees: dict[str, int] = {}
    for transfer in career.world_transfers:
        buyer = transfer["to_club_id"]
        fees[buyer] = fees.get(buyer, 0) + int(transfer["fee"])
    for club in clubs:
        club_id = str(club["id"])
        initial_value = sum(
            int(player["market_value"]) for player in squads[club_id]
        )
        assert fees.get(club_id, 0) <= initial_value * 0.10

    for club in clubs:
        club_id = str(club["id"])
        final = effective_players(
            career,
            club_id,
            squads[club_id],
            lookup_for(*squads.values(), free_agents),
        )
        assert SQUAD_MIN <= len(final) <= SQUAD_MAX


def test_deals_belong_to_their_batch_period():
    clubs = make_clubs()
    squads = make_world(clubs)
    free_agents = make_free_agents()
    career = make_career(seed=7)
    advance_world_market(
        career,
        clubs,
        squads,
        free_agents,
        previous_date="2026-06-30",
        target_date="2026-08-31",
        player_lookup=lookup_for(*squads.values(), free_agents),
    )
    batches = batch_schedule("2026-07-01", "2026-08-31")
    for transfer in career.world_transfers:
        match = [
            batch
            for batch in batches
            if batch["period_start"] <= transfer["date"] <= batch["period_end"]
        ]
        assert len(match) == 1, transfer


def test_free_agents_join_for_zero_fee():
    clubs = make_clubs()
    squads = make_world(clubs, size=17)
    free_agents = make_free_agents(20)
    career = make_career(seed=11)
    advance_world_market(
        career,
        clubs,
        squads,
        free_agents,
        previous_date="2026-06-30",
        target_date="2026-08-31",
        player_lookup=lookup_for(*squads.values(), free_agents),
    )
    free_deals = [
        transfer for transfer in career.world_transfers if transfer["kind"] == "free_agent"
    ]
    assert free_deals
    assert all(transfer["fee"] == 0 for transfer in free_deals)
    assert all(transfer["from_club_id"] is None for transfer in free_deals)
    for club in clubs:
        club_id = str(club["id"])
        final = effective_players(
            career,
            club_id,
            squads[club_id],
            lookup_for(*squads.values(), free_agents),
        )
        assert len(final) >= SQUAD_MIN


def test_needs_are_calculated_from_current_players_only():
    players = make_players("c0", 10)
    assert role_counts(players)
    assert club_budget(players) == int(
        sum(player["market_value"] for player in players) * 0.10
    )
    assert not hasattr(make_career(), "needs")


def test_deltas_are_persisted_and_shape_effective_squad():
    clubs = make_clubs()
    squads = make_world(clubs)
    free_agents = make_free_agents()
    career = make_career(seed=3)
    advance_world_market(
        career,
        clubs,
        squads,
        free_agents,
        previous_date="2026-06-30",
        target_date="2026-08-31",
        player_lookup=lookup_for(*squads.values(), free_agents),
    )
    assert career.club_deltas
    for club_id, delta in career.club_deltas.items():
        assert set(delta) == {"in", "out"}
        effective = effective_players(
            career,
            club_id,
            squads.get(club_id, []),
            lookup_for(*squads.values(), free_agents),
        )
        ids = {str(player["id"]) for player in effective}
        assert not ids.intersection(delta["out"])

    saved = career.to_save()
    assert "world_transfers" in saved
    assert "club_deltas" in saved
    assert "needs" not in saved
    assert saved["world_market_date"] == "2026-08-31"

    from server.career.core import Career

    restored = Career.from_save(saved)
    assert restored.world_transfers == career.world_transfers
    assert restored.club_deltas == career.club_deltas
    assert restored.world_market_date == career.world_market_date


def test_old_save_without_world_market_fields_loads():
    from server.career.core import Career

    career = make_career()
    saved = career.to_save()
    saved.pop("world_market_date", None)
    saved.pop("world_transfers", None)
    saved.pop("club_deltas", None)
    restored = Career.from_save(saved)
    assert restored.world_market_date is None
    assert restored.world_transfers == []
    assert restored.club_deltas == {}


def test_deltas_change_opponent_strength_in_snapshot(
    client: TestClient, saves_dir
):
    response = client.post(
        "/api/careers",
        json={
            "club_id": ARSENAL,
            "manager_name": "Strength Tester",
            "manager_nationality_id": ENGLAND,
            "seed": 4242,
        },
    )
    assert response.status_code == 201, response.text
    career = response.json()
    opponent = career["season"]["next"]["opponent"]
    before = opponent["strength"]

    path = saves_dir / f"{career['id']}.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    squad = client.app.state.canon.squad(opponent["id"])
    strongest = sorted(squad, key=lambda player: -player["overall"])[:11]
    raw.setdefault("club_deltas", {}).setdefault(
        opponent["id"], {"in": [], "out": []}
    )
    raw["club_deltas"][opponent["id"]]["out"] = list(
        dict.fromkeys(
            raw["club_deltas"][opponent["id"]]["out"]
            + [str(player["id"]) for player in strongest]
        )
    )
    raw["world_market_date"] = raw["date"]
    path.write_text(json.dumps(raw), encoding="utf-8")

    updated = client.get(f"/api/careers/{career['id']}")
    assert updated.status_code == 200, updated.text
    assert updated.json()["season"]["next"]["opponent"]["strength"] < before


def null_or_str(value):
    return "" if value is None else str(value)
