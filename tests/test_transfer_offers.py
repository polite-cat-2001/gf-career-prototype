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
            "manager_name": "Offer Tester",
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


def advance_days(client: TestClient, career_id: str, days: int) -> dict:
    current = date.fromisoformat(career_state(client, career_id)["date"])
    target = (current + timedelta(days=days)).isoformat()
    return action(client, career_id, {"type": "advance", "date": target})


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


def pick_player(client: TestClient, career: dict) -> dict:
    canon = client.app.state.canon
    own = set(career["player_ids"]) if "player_ids" in career else {
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


def pick_players(client: TestClient, career: dict, count: int) -> list[dict]:
    canon = client.app.state.canon
    own = {
        player["id"]
        for group in career["squad"]["groups"]
        for player in group["players"]
    }
    players, _ = canon.search_players(
        limit=100, sort="value", direction="asc", age_min=18
    )
    picked = []
    for player in players:
        if player["id"] in own or not player.get("club_id"):
            continue
        if int(player.get("market_value") or 0) > 10_000:
            continue
        picked.append(player)
        if len(picked) == count:
            return picked
    raise AssertionError("not enough cheap external players found")


def sent_offers(career: dict) -> list[dict]:
    return career["transfers"]["sent_offers"]


def offer_for(career: dict, player_id: str) -> dict:
    return next(
        offer
        for offer in reversed(sent_offers(career))
        if offer["id"] == player_id
    )


def test_transfer_offer_appears_in_sent_offers(client: TestClient):
    career = create_career(client)
    player = pick_player(client, career)

    updated = action(
        client,
        career["id"],
        {"type": "transfer_offer", "player_id": player["id"], "amount": 100_000},
    )
    offers = sent_offers(updated)
    assert len(offers) == 1
    offer = offers[0]
    assert offer["id"] == player["id"]
    assert offer["kind"] == "transfer"
    assert offer["amount"] == 100_000
    assert offer["status"] == "pending"
    assert offer["can_offer_again"] is False
    assert offer["message"]
    assert offer["due"] > updated["date"]


def test_loan_offer_stores_fee_and_wage_share(client: TestClient):
    career = create_career(client)
    player = pick_player(client, career)

    updated = action(
        client,
        career["id"],
        {
            "type": "loan_offer",
            "player_id": player["id"],
            "loan_fee": 50_000,
            "wage_share": 60,
        },
    )
    offer = sent_offers(updated)[0]
    assert offer["kind"] == "loan"
    assert offer["loan_fee"] == 50_000
    assert offer["wage_share"] == 60
    assert offer["amount"] == 50_000


def test_offer_validation_rejects_bad_inputs(client: TestClient):
    career = create_career(client)
    own = career["squad"]["groups"][0]["players"][0]["id"]
    balance = career["squad"]["finance"]["balance"]

    cases = [
        {"type": "transfer_offer", "player_id": "does-not-exist", "amount": 1},
        {"type": "transfer_offer", "player_id": own, "amount": 1},
        {"type": "transfer_offer", "player_id": pick_player(client, career)["id"], "amount": -1},
        {
            "type": "transfer_offer",
            "player_id": pick_player(client, career)["id"],
            "amount": balance + 1,
        },
        {
            "type": "loan_offer",
            "player_id": pick_player(client, career)["id"],
            "loan_fee": 1,
            "wage_share": 150,
        },
        {
            "type": "loan_offer",
            "player_id": pick_player(client, career)["id"],
            "loan_fee": 1,
            "wage_share": 50,
            "buyout": True,
        },
    ]
    for payload in cases:
        response = client.post(
            f"/api/careers/{career['id']}/actions", json=payload
        )
        assert response.status_code == 422, (payload, response.text)

    player_id = pick_player(client, career)["id"]
    action(
        client,
        career["id"],
        {"type": "transfer_offer", "player_id": player_id, "amount": 50_000},
    )
    duplicate = client.post(
        f"/api/careers/{career['id']}/actions",
        json={"type": "transfer_offer", "player_id": player_id, "amount": 60_000},
    )
    assert duplicate.status_code == 422, duplicate.text


def test_ai_answers_only_at_due_and_is_deterministic(client: TestClient):
    first = create_career(client)
    second = create_career(client)
    player = pick_player(client, first)
    payload = {"type": "transfer_offer", "player_id": player["id"], "amount": 40_000}

    first_offer = sent_offers(action(client, first["id"], payload))[0]
    second_offer = sent_offers(action(client, second["id"], payload))[0]
    assert first_offer["offer_id"] == second_offer["offer_id"]
    assert first_offer["due"] == second_offer["due"]

    delay = (
        date.fromisoformat(first_offer["due"]) - date.fromisoformat(first["date"])
    ).days
    assert 2 <= delay <= 4

    early = advance_days(client, first["id"], delay - 1)
    assert offer_for(early, player["id"])["status"] == "pending"

    resolved = advance_days(client, first["id"], 1)
    assert offer_for(resolved, player["id"])["status"] != "pending"

    second_resolved = advance_days(client, second["id"], delay)
    assert offer_for(second_resolved, player["id"])["status"] == offer_for(
        resolved, player["id"]
    )["status"]


def test_ai_can_accept_refuse_or_counter(client: TestClient):
    career = create_career(client)
    accept_player, counter_player, refuse_player = pick_players(client, career, 3)

    for player, amount in (
        (accept_player, 100_000),
        (counter_player, 40_000),
        (refuse_player, 0),
    ):
        action(
            client,
            career["id"],
            {"type": "transfer_offer", "player_id": player["id"], "amount": amount},
        )

    updated = advance_days(client, career["id"], 4)
    assert offer_for(updated, accept_player["id"])["status"] == "accepted"
    assert offer_for(updated, counter_player["id"])["status"] == "counter"
    assert offer_for(updated, refuse_player["id"])["status"] == "refused"
    assert offer_for(updated, counter_player["id"])["counter"]["amount"] > 0


def test_buyout_offer_uses_release_clause_and_is_accepted(client: TestClient):
    career = create_career(client)
    player = pick_player(client, career)

    updated = action(
        client,
        career["id"],
        {"type": "transfer_offer", "player_id": player["id"], "buyout": True},
    )
    offer = sent_offers(updated)[0]
    assert offer["buyout"] is True
    assert offer["amount"] == offer["release_clause"]

    resolved = advance_days(client, career["id"], 4)
    assert offer_for(resolved, player["id"])["status"] == "accepted"


def test_two_counters_then_refusal_and_seven_day_retry(
    client: TestClient, saves_dir: Path
):
    career = create_career(client)
    player = pick_player(client, career)
    payload = {"type": "transfer_offer", "player_id": player["id"], "amount": 40_000}

    first = sent_offers(action(client, career["id"], payload))[0]
    updated = set_date(client, saves_dir, career["id"], first["due"])
    first_counter = offer_for(updated, player["id"])
    assert first_counter["status"] == "counter"
    assert first_counter["counter_offers"] == 1

    action(client, career["id"], payload)
    second_due = offer_for(career_state(client, career["id"]), player["id"])["due"]
    updated = set_date(client, saves_dir, career["id"], second_due)
    second_counter = offer_for(updated, player["id"])
    assert second_counter["status"] == "counter"
    assert second_counter["counter_offers"] == 2

    action(client, career["id"], payload)
    third_due = offer_for(career_state(client, career["id"]), player["id"])["due"]
    refused = set_date(client, saves_dir, career["id"], third_due)
    refused_offer = offer_for(refused, player["id"])
    assert refused_offer["status"] == "refused"
    assert refused_offer["retry_after"]
    assert refused_offer["can_offer_again"] is False

    blocked = client.post(
        f"/api/careers/{career['id']}/actions", json=payload
    )
    assert blocked.status_code == 422, blocked.text

    ready = set_date(
        client, saves_dir, career["id"], refused_offer["retry_after"]
    )
    assert offer_for(ready, player["id"])["can_offer_again"] is True
    retried = action(client, career["id"], payload)
    retried_offer = offer_for(retried, player["id"])
    assert retried_offer["status"] == "pending"
    assert retried_offer["offer_id"] != first["offer_id"]


def test_accept_counter_offer(client: TestClient):
    career = create_career(client)
    player = pick_player(client, career)

    updated = action(
        client,
        career["id"],
        {"type": "transfer_offer", "player_id": player["id"], "amount": 40_000},
    )
    assert sent_offers(updated)[0]["status"] == "pending"

    countered = advance_days(client, career["id"], 4)
    offer = offer_for(countered, player["id"])
    assert offer["status"] == "counter"
    assert offer["can_accept_counter"] is True
    assert offer["can_offer_again"] is True

    accepted = action(
        client,
        career["id"],
        {"type": "accept_offer_counter", "offer_id": offer["offer_id"]},
    )
    final = offer_for(accepted, player["id"])
    assert final["status"] == "accepted"
    assert final["can_accept_counter"] is False


def test_offers_survive_load_and_next_season(
    client: TestClient, saves_dir: Path
):
    career = create_career(client)
    player = pick_player(client, career)
    action(
        client,
        career["id"],
        {"type": "transfer_offer", "player_id": player["id"], "amount": 100_000},
    )

    loaded = career_state(client, career["id"])
    assert len(sent_offers(loaded)) == 1

    path = saves_dir / f"{career['id']}.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["results"] = {fixture["id"]: {"home": 1, "away": 0} for fixture in raw["schedule"]}
    raw["date"] = "2027-03-01"
    path.write_text(json.dumps(raw), encoding="utf-8")

    response = client.post(
        f"/api/careers/{career['id']}/actions", json={"type": "next_season"}
    )
    assert response.status_code == 200, response.text
    started = response.json()
    assert started["season"]["season_start"] == "2027-07-01"
    assert len(sent_offers(started)) == 1

    saved = json.loads(path.read_text(encoding="utf-8"))
    assert len(saved["transfer_offers"]) == 1


def test_old_save_without_transfer_offers_loads(client: TestClient, saves_dir: Path):
    career = create_career(client)
    path = saves_dir / f"{career['id']}.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw.pop("transfer_offers", None)
    path.write_text(json.dumps(raw), encoding="utf-8")

    loaded = client.get(f"/api/careers/{career['id']}")
    assert loaded.status_code == 200, loaded.text
    assert loaded.json()["transfers"]["sent_offers"] == []


def test_new_offer_replaces_old_and_sent_offers_are_newest_first(
    client: TestClient, saves_dir: Path
):
    career = create_career(client)
    first_player, second_player = pick_players(client, career, 2)

    first = sent_offers(
        action(
            client,
            career["id"],
            {
                "type": "transfer_offer",
                "player_id": first_player["id"],
                "amount": 0,
            },
        )
    )[0]
    action(
        client,
        career["id"],
        {
            "type": "transfer_offer",
            "player_id": second_player["id"],
            "amount": 100_000,
        },
    )
    ordered = sent_offers(career_state(client, career["id"]))
    assert [offer["id"] for offer in ordered] == [
        second_player["id"],
        first_player["id"],
    ]

    refused = set_date(client, saves_dir, career["id"], first["due"])
    refused_offer = offer_for(refused, first_player["id"])
    assert refused_offer["status"] == "refused"

    set_date(client, saves_dir, career["id"], refused_offer["retry_after"])
    replaced = action(
        client,
        career["id"],
        {
            "type": "transfer_offer",
            "player_id": first_player["id"],
            "amount": 100_000,
        },
    )
    offers = sent_offers(replaced)
    assert [offer["id"] for offer in offers].count(first_player["id"]) == 1
    assert offers[0]["id"] == first_player["id"]
    assert offers[0]["status"] == "pending"


def test_old_save_with_duplicate_offers_keeps_latest(
    client: TestClient, saves_dir: Path
):
    career = create_career(client)
    player = pick_player(client, career)
    action(
        client,
        career["id"],
        {"type": "transfer_offer", "player_id": player["id"], "amount": 50_000},
    )

    path = saves_dir / f"{career['id']}.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["transfer_offers"].append(dict(raw["transfer_offers"][0]))
    path.write_text(json.dumps(raw), encoding="utf-8")

    loaded = career_state(client, career["id"])
    offers = sent_offers(loaded)
    assert [offer["id"] for offer in offers].count(player["id"]) == 1
