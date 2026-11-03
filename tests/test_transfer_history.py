from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

ARSENAL = "11"
ENGLAND = "189"


def create_career(client: TestClient, seed: int = 4242) -> dict:
    response = client.post(
        "/api/careers",
        json={
            "club_id": ARSENAL,
            "manager_name": "History Tester",
            "manager_nationality_id": ENGLAND,
            "seed": seed,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def action(client: TestClient, career_id: str, payload: dict) -> dict:
    response = client.post(f"/api/careers/{career_id}/actions", json=payload)
    assert response.status_code == 200, response.text
    return response.json()


def career_state(client: TestClient, career_id: str) -> dict:
    response = client.get(f"/api/careers/{career_id}")
    assert response.status_code == 200, response.text
    return response.json()


def set_date(
    client: TestClient, saves_dir: Path, career_id: str, target: str
) -> dict:
    path = saves_dir / f"{career_id}.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["date"] = target
    path.write_text(json.dumps(raw), encoding="utf-8")
    response = client.post(f"/api/careers/{career_id}/save")
    assert response.status_code == 200, response.text
    return response.json()


def pick_external_player(client: TestClient, career: dict) -> dict:
    canon = client.app.state.canon
    own = {
        player["id"]
        for group in career["squad"]["groups"]
        for player in group["players"]
    }
    players, _ = canon.search_players(
        limit=50, sort="value", direction="asc", age_min=18
    )
    for player in players:
        if player["id"] in own or not player.get("club_id"):
            continue
        if int(player.get("market_value") or 0) <= 10_000:
            return player
    raise AssertionError("no cheap external player found")


def history(career: dict) -> list[dict]:
    return career["transfers"]["history"]


def find_entry(career: dict, player_id: str, source: str | None = None) -> dict:
    for entry in history(career):
        if entry["player_id"] != player_id:
            continue
        if source is None or entry["source"] == source:
            return entry
    raise AssertionError(f"no history entry for {player_id} ({source})")


def test_world_transfers_are_in_history_with_price_and_rating(client: TestClient):
    career = create_career(client)
    entries = history(career)
    assert entries
    assert all(isinstance(entry["fee"], int) and entry["fee"] >= 0 for entry in entries)
    assert all(entry["overall"] > 0 for entry in entries)
    assert any(entry["source"] == "world" for entry in entries)
    assert any(entry["kind"] == "free_agent" and entry["fee"] == 0 for entry in entries)
    assert all(
        entries[index]["overall"] >= entries[index + 1]["overall"]
        for index in range(len(entries) - 1)
    )


def test_pending_offers_are_not_completed_deals(client: TestClient):
    career = create_career(client)
    player = pick_external_player(client, career)
    updated = action(
        client,
        career["id"],
        {"type": "transfer_offer", "player_id": player["id"], "amount": 100_000},
    )
    assert all(item["player_id"] != player["id"] for item in history(updated))
    assert all(item["source"] != "sent" for item in history(updated))

    club = client.get(
        f"/api/careers/{career['id']}/transfers/history?filter=club"
    )
    assert club.status_code == 200, club.text
    assert club.json()["items"] == []

    league = client.get(
        f"/api/careers/{career['id']}/transfers/history?filter=league"
    ).json()
    assert all(item["in_my_league"] for item in league["items"])

    invalid = client.get(
        f"/api/careers/{career['id']}/transfers/history?filter=nope"
    )
    assert invalid.status_code == 422


def test_accepted_incoming_offer_keeps_seller_and_buyer_on_correct_sides(
    client: TestClient,
):
    career = create_career(client)
    updated = action(
        client, career["id"], {"type": "advance", "date": "2026-07-07"}
    )
    received = updated["transfers"]["received_offers"]
    assert received
    offer = received[0]
    accepted = action(
        client,
        career["id"],
        {"type": "incoming_accept", "offer_id": offer["offer_id"]},
    )
    assert all(
        item["offer_id"] != offer["offer_id"]
        for item in accepted["transfers"]["received_offers"]
    )
    entries = [
        item
        for item in history(accepted)
        if item["player_id"] == offer["id"] and item["source"] == "manager"
    ]
    assert len(entries) == 1
    entry = entries[0]
    assert entry["from_club_id"] == career["club"]["id"]
    assert entry["to_club_id"] == offer["club_id"]
    assert entry["from_club_name"] == career["club"]["name"]
    assert entry["to_club_name"] == offer["club_name"]
    assert entry["fee"] == offer["amount"]
    assert entry["kind"] == offer["kind"]
    assert entry["overall"] > 0


def test_executed_incoming_offer_is_backfilled_in_history(
    client: TestClient, saves_dir: Path
):
    career = create_career(client)
    updated = action(
        client, career["id"], {"type": "advance", "date": "2026-07-07"}
    )
    offer = updated["transfers"]["received_offers"][0]
    accepted = action(
        client,
        career["id"],
        {"type": "incoming_accept", "offer_id": offer["offer_id"]},
    )

    path = saves_dir / f"{career['id']}.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw.pop("transfer_history", None)
    path.write_text(json.dumps(raw), encoding="utf-8")

    restored = career_state(client, career["id"])
    entries = [
        item
        for item in history(restored)
        if item["player_id"] == offer["id"] and item["source"] == "manager"
    ]
    assert len(entries) == 1
    assert entries[0]["from_club_id"] == career["club"]["id"]
    assert entries[0]["to_club_id"] == offer["club_id"]
    assert entries[0]["fee"] == offer["amount"]
    assert all(
        item["offer_id"] != offer["offer_id"]
        for item in accepted["transfers"]["received_offers"]
    )
    assert all(
        item["offer_id"] != offer["offer_id"]
        for item in restored["transfers"]["received_offers"]
    )


def test_free_agent_signing_is_recorded_with_zero_fee(
    client: TestClient, saves_dir: Path
):
    career = create_career(client)
    canon = client.app.state.canon
    own = {
        player["id"]
        for group in career["squad"]["groups"]
        for player in group["players"]
    }
    free_agents, _ = canon.search_players(free_only=True, limit=20, age_min=18)
    player = next(item for item in free_agents if item["id"] not in own)

    started = action(
        client,
        career["id"],
        {
            "type": "transfer_contract",
            "player_id": player["id"],
            "years": 1,
            "weekly_wage": 1_000,
            "squad_role": "prospect",
            "release_clause": 0,
        },
    )
    state = started["transfers"]["contracts"][player["id"]]
    updated = set_date(client, saves_dir, career["id"], state["due"])
    state = updated["transfers"]["contracts"][player["id"]]
    if state["status"] == "counter":
        updated = action(
            client,
            career["id"],
            {"type": "transfer_accept_counter", "player_id": player["id"]},
        )
    signed = action(
        client,
        career["id"],
        {"type": "transfer_sign", "player_id": player["id"]},
    )
    entry = find_entry(signed, player["id"], "manager")
    assert entry["fee"] == 0
    assert entry["kind"] == "free"
    assert entry["to_club_id"] == career["club"]["id"]
    assert entry["from_club_id"] is None
    assert entry["overall"] > 0
    assert entry["with_manager"] is True

    club = client.get(
        f"/api/careers/{career['id']}/transfers/history?filter=club"
    )
    assert club.status_code == 200, club.text
    items = club.json()["items"]
    assert items
    assert all(item["with_manager"] for item in items)
    assert any(item["player_id"] == player["id"] for item in items)


def test_history_fields_survive_save_and_load(client: TestClient):
    career = create_career(client)
    before = career_state(client, career["id"])["transfers"]["history"]
    assert before
    response = client.post(f"/api/careers/{career['id']}/save")
    assert response.status_code == 200, response.text
    after = response.json()["transfers"]["history"]
    assert after == before
