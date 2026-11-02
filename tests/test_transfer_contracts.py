from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

from fastapi.testclient import TestClient

ARSENAL = "11"
ENGLAND = "189"


def create_career(client: TestClient, seed: int = 4242) -> dict:
    response = client.post(
        "/api/careers",
        json={
            "club_id": ARSENAL,
            "manager_name": "Contract Tester",
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


def squad_ids(career: dict) -> set[str]:
    return {
        player["id"]
        for group in career["squad"]["groups"]
        for player in group["players"]
    }


def squad_player(career: dict, player_id: str) -> dict | None:
    for group in career["squad"]["groups"]:
        for player in group["players"]:
            if player["id"] == player_id:
                return player
    return None


def pick_external_player(client: TestClient, career: dict) -> dict:
    canon = client.app.state.canon
    own = squad_ids(career)
    players, _ = canon.search_players(
        limit=50, sort="value", direction="asc", age_min=18
    )
    for player in players:
        if player["id"] in own or not player.get("club_id"):
            continue
        if int(player.get("market_value") or 0) <= 10_000:
            return player
    raise AssertionError("no cheap external player found")


def accepted_offer(client: TestClient, career: dict, player: dict) -> dict:
    updated = action(
        client,
        career["id"],
        {"type": "transfer_offer", "player_id": player["id"], "buyout": True},
    )
    offer = updated["transfers"]["sent_offers"][0]
    updated = action(
        client, career["id"], {"type": "advance", "date": offer["due"]}
    )
    accepted = updated["transfers"]["sent_offers"][0]
    assert accepted["status"] == "accepted", accepted
    return accepted


def lowball_contract(client: TestClient, career: dict, player: dict, offer_id: str | None):
    payload = {
        "type": "transfer_contract",
        "player_id": player["id"],
        "years": 1,
        "weekly_wage": 1_000,
        "squad_role": "prospect",
        "release_clause": 0,
    }
    if offer_id:
        payload["offer_id"] = offer_id
    return action(client, career["id"], payload)


def contract_state(career: dict, player_id: str) -> dict:
    return career["transfers"]["contracts"][player_id]


def test_contract_screen_starts_after_club_accepts_offer(client: TestClient):
    career = create_career(client)
    player = pick_external_player(client, career)
    offer = accepted_offer(client, career, player)

    assert offer["can_negotiate"] is True
    assert offer["signed"] is False
    assert offer["contract_status"] is None
    assert offer["transfer_contract"] is None
    defaults = offer["contract_defaults"]
    assert 1 <= defaults["years"] <= 5
    assert defaults["weekly_wage"] > 0
    assert defaults["release_clause"] > 0

    search = client.get(
        f"/api/careers/{career['id']}/transfers/search"
        "?limit=100&sort=value&direction=asc"
    ).json()
    listed = next(item for item in search["items"] if item["id"] == player["id"])
    assert listed["latest_offer"]["can_negotiate"] is True
    assert listed["latest_offer"]["offer_id"] == offer["offer_id"]

    updated = lowball_contract(client, career, player, offer["offer_id"])
    state = contract_state(updated, player["id"])
    assert state["status"] == "pending"
    assert state["kind"] == "transfer"
    assert state["fee"] == offer["amount"]
    assert state["balance_after"] == (
        updated["squad"]["finance"]["balance"] - offer["amount"]
    )
    assert state["offer"]["weekly_wage"] == 1_000
    assert state["offer"]["years"] == 1
    assert state["can_sign"] is False


def test_player_counter_is_exact_and_manual_signature_completes_transfer(
    client: TestClient, saves_dir: Path
):
    career = create_career(client)
    player = pick_external_player(client, career)
    offer = accepted_offer(client, career, player)
    balance_before = career_state(client, career["id"])["squad"]["finance"]["balance"]

    started = lowball_contract(client, career, player, offer["offer_id"])
    due = contract_state(started, player["id"])["due"]
    countered = set_date(client, saves_dir, career["id"], due)
    state = contract_state(countered, player["id"])
    assert state["status"] == "counter"
    assert state["counter_offers"] == 1
    assert set(state["counter"]) == {
        "years",
        "weekly_wage",
        "squad_role",
        "release_clause",
    }
    assert state["counter"]["release_clause"] > 0
    assert player["id"] not in squad_ids(countered)

    accepted = action(
        client,
        career["id"],
        {"type": "transfer_accept_counter", "player_id": player["id"]},
    )
    state = contract_state(accepted, player["id"])
    assert state["status"] == "accepted"
    assert state["terms"] == state["counter"] or state["terms"] == state["agreed"]
    assert state["can_sign"] is True

    signed = action(
        client,
        career["id"],
        {"type": "transfer_sign", "player_id": player["id"]},
    )
    joined = squad_player(signed, player["id"])
    assert joined is not None
    assert 1 <= joined["shirt_number"] <= 99
    assert joined["contract"]["years"] == state["agreed"]["years"]
    assert joined["contract"]["weekly_wage"] == state["agreed"]["weekly_wage"]
    assert signed["squad"]["finance"]["balance"] == balance_before - offer["amount"]
    assert player["id"] not in signed["transfers"]["contracts"]
    assert signed["transfers"]["sent_offers"] == []


def test_signing_is_blocked_when_balance_is_short(
    client: TestClient, saves_dir: Path
):
    career = create_career(client)
    player = pick_external_player(client, career)
    offer = accepted_offer(client, career, player)

    started = lowball_contract(client, career, player, offer["offer_id"])
    due = contract_state(started, player["id"])["due"]
    countered = set_date(client, saves_dir, career["id"], due)
    assert contract_state(countered, player["id"])["status"] == "counter"
    action(
        client,
        career["id"],
        {"type": "transfer_accept_counter", "player_id": player["id"]},
    )

    path = saves_dir / f"{career['id']}.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["balance"] = 0
    path.write_text(json.dumps(raw), encoding="utf-8")

    snapshot = career_state(client, career["id"])
    state = contract_state(snapshot, player["id"])
    assert state["status"] == "accepted"
    assert state["affordable"] is False
    assert state["can_sign"] is False

    response = client.post(
        f"/api/careers/{career['id']}/actions",
        json={"type": "transfer_sign", "player_id": player["id"]},
    )
    assert response.status_code == 422, response.text
    assert player["id"] not in squad_ids(career_state(client, career["id"]))


def test_free_agent_skips_club_screen_and_joins_squad(
    client: TestClient, saves_dir: Path
):
    career = create_career(client)
    canon = client.app.state.canon
    own = squad_ids(career)
    players, _ = canon.search_players(free_only=True, limit=20, age_min=18)
    player = next(item for item in players if item["id"] not in own)
    assert not player.get("club_id")

    started = lowball_contract(client, career, player, None)
    state = contract_state(started, player["id"])
    assert state["kind"] == "free"
    assert state["fee"] == 0
    assert state["balance_after"] == started["squad"]["finance"]["balance"]

    due = state["due"]
    updated = set_date(client, saves_dir, career["id"], due)
    state = contract_state(updated, player["id"])
    if state["status"] == "counter":
        updated = action(
            client,
            career["id"],
            {"type": "transfer_accept_counter", "player_id": player["id"]},
        )
    assert contract_state(updated, player["id"])["status"] == "accepted"

    signed = action(
        client,
        career["id"],
        {"type": "transfer_sign", "player_id": player["id"]},
    )
    joined = squad_player(signed, player["id"])
    assert joined is not None
    assert 1 <= joined["shirt_number"] <= 99
    assert signed["transfers"]["sent_offers"] == []


def test_signed_transfer_outside_window_executes_when_it_opens(
    client: TestClient, saves_dir: Path
):
    career = create_career(client)
    player = pick_external_player(client, career)
    offer = accepted_offer(client, career, player)

    set_date(client, saves_dir, career["id"], "2026-09-01")
    started = lowball_contract(client, career, player, offer["offer_id"])
    due = contract_state(started, player["id"])["due"]
    countered = set_date(client, saves_dir, career["id"], due)
    assert contract_state(countered, player["id"])["status"] == "counter"
    action(
        client,
        career["id"],
        {"type": "transfer_accept_counter", "player_id": player["id"]},
    )

    signed = action(
        client,
        career["id"],
        {"type": "transfer_sign", "player_id": player["id"]},
    )
    assert player["id"] not in squad_ids(signed)
    assert len(signed["transfers"]["pending"]) == 1
    pending = signed["transfers"]["pending"][0]
    assert pending["player_id"] == player["id"]
    assert pending["execute_on"] == "2027-01-01"
    final_offer = signed["transfers"]["sent_offers"][0]
    assert final_offer["signed"] is True
    assert final_offer["execute_on"] == "2027-01-01"

    set_date(client, saves_dir, career["id"], "2027-01-01")
    loaded = career_state(client, career["id"])
    joined = squad_player(loaded, player["id"])
    assert joined is not None
    assert 1 <= joined["shirt_number"] <= 99
    assert loaded["transfers"]["pending"] == []
    assert loaded["transfers"]["sent_offers"] == []


def test_contract_rejects_players_without_free_agent_status(client: TestClient):
    career = create_career(client)
    own_player = career["squad"]["groups"][0]["players"][0]
    response = client.post(
        f"/api/careers/{career['id']}/actions",
        json={
            "type": "transfer_contract",
            "player_id": own_player["id"],
            "years": 3,
            "weekly_wage": 10_000,
            "squad_role": "rotation",
            "release_clause": 1_000_000,
        },
    )
    assert response.status_code == 422, response.text

    search = client.get(
        f"/api/careers/{career['id']}/transfers/search?limit=100&sort=value&direction=asc"
    ).json()
    current = date.fromisoformat(career["date"])
    external = None
    for item in search["items"]:
        expires = item.get("contract_expires")
        if not expires or not item.get("club_id"):
            continue
        remaining = date.fromisoformat(expires) - current
        if remaining > timedelta(days=190):
            external = item
            break
    assert external is not None

    response = client.post(
        f"/api/careers/{career['id']}/actions",
        json={
            "type": "transfer_contract",
            "player_id": external["id"],
            "years": 3,
            "weekly_wage": 10_000,
            "squad_role": "rotation",
            "release_clause": 1_000_000,
        },
    )
    assert response.status_code == 422, response.text


def test_scout_report_player_keeps_offer_state_for_same_action_modal(
    client: TestClient, saves_dir: Path
):
    career = create_career(client)
    player = pick_external_player(client, career)
    offer = accepted_offer(client, career, player)
    scout_id = career_state(client, career["id"])["scouting"]["scouts"][0]["id"]

    path = saves_dir / f"{career['id']}.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["scout_reports"] = {
        player["id"]: {
            "scout_id": scout_id,
            "completed_at": raw["date"],
            "acknowledged": False,
        }
    }
    path.write_text(json.dumps(raw), encoding="utf-8")

    snapshot = career_state(client, career["id"])
    entry = next(
        item
        for item in snapshot["scouting"]["reports"]
        if item["player"]["id"] == player["id"]
    )
    latest = entry["player"]["latest_offer"]
    assert latest["offer_id"] == offer["offer_id"]
    assert latest["can_negotiate"] is True
