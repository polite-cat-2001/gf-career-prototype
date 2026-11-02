from __future__ import annotations

from datetime import date, timedelta

from fastapi.testclient import TestClient

from server.career import create_career
from server.career.incoming_offers import (
    accept_incoming_offer,
    counter_incoming_offer,
    execute_pending_departures,
    generate_incoming_offers,
    resolve_incoming_offers,
)

ARSENAL = "11"
ENGLAND = "189"
FRANCE = "50"


def create_api_career(client: TestClient, seed: int = 4242) -> dict:
    response = client.post(
        "/api/careers",
        json={
            "club_id": ARSENAL,
            "manager_name": "Incoming Tester",
            "manager_nationality_id": ENGLAND,
            "seed": seed,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def advance_days(client: TestClient, career_id: str, days: int) -> dict:
    current = date.fromisoformat(
        client.get(f"/api/careers/{career_id}").json()["date"]
    )
    target = (current + timedelta(days=days)).isoformat()
    response = client.post(
        f"/api/careers/{career_id}/actions",
        json={"type": "advance", "date": target},
    )
    assert response.status_code == 200, response.text
    return response.json()


def received(career: dict) -> list[dict]:
    return career["transfers"]["received_offers"]


def make_career(player_count: int = 12, seed: int = 7):
    player_ids = [f"p{index}" for index in range(player_count)]
    career = create_career(
        manager_name="Test",
        manager_nationality_id=ENGLAND,
        manager_nationality="England",
        club_id=ARSENAL,
        player_ids=player_ids,
        seed=seed,
    )
    career.balance = 0
    return career


def players(player_count: int, overall: float = 80.0) -> list[dict]:
    return [
        {
            "id": f"p{index}",
            "name": f"Player {index}",
            "role": "CF",
            "overall": overall,
            "market_value": 10_000_000,
            "age": 25,
            "club_id": ARSENAL,
            "club_name": "Arsenal",
        }
        for index in range(player_count)
    ]


def clubs() -> list[dict]:
    return [
        {
            "id": ARSENAL,
            "name": "Arsenal",
            "country_id": ENGLAND,
            "country_name": "England",
            "league_name": "Premier League",
            "tier_rank": 1,
        },
        {
            "id": "domestic",
            "name": "Domestic FC",
            "country_id": ENGLAND,
            "country_name": "England",
            "league_name": "Championship",
            "tier_rank": 2,
        },
        {
            "id": "foreign",
            "name": "Foreign FC",
            "country_id": FRANCE,
            "country_name": "France",
            "league_name": "Ligue 1",
            "tier_rank": 1,
        },
    ]


def roles() -> dict[str, dict[str, dict]]:
    return {
        ARSENAL: {"CF": {"count": 3, "best": 80.0}},
        "domestic": {"CF": {"count": 1, "best": 55.0}},
        "foreign": {"CF": {"count": 1, "best": 55.0}},
    }


def test_ai_sends_one_or_two_offers_in_a_window_week(client: TestClient):
    career = create_api_career(client)
    updated = advance_days(client, career["id"], 6)
    offers = received(updated)
    assert 1 <= len(offers) <= 2
    for offer in offers:
        assert offer["status"] == "pending"
        assert offer["unread"] is True
        assert offer["club_name"]
        assert offer["expires_at"]
        expires = date.fromisoformat(offer["expires_at"])
        created = date.fromisoformat(offer["created_at"])
        assert (expires - created).days == 30
    pairs = [(offer["id"], offer["club_id"]) for offer in offers]
    assert len(pairs) == len(set(pairs))


def test_foreign_clubs_only_bid_for_players_above_threshold(client: TestClient):
    career = create_api_career(client)
    updated = advance_days(client, career["id"], 6)
    own_country = updated["club"]["country_id"]
    for offer in received(updated):
        if offer["club_country_name"] and offer["club_country_id"] != own_country:
            assert offer["overall"] >= 75.0


def test_window_pace_is_one_to_two_per_week_and_one_per_fortnight_outside():
    career = make_career()
    squad = players(12)
    generate_incoming_offers(
        career, "2026-07-01", "2026-07-07", squad, clubs(), roles()
    )
    assert 1 <= len(career.incoming_offers) <= 2

    outside = make_career()
    generate_incoming_offers(
        outside, "2026-09-01", "2026-09-14", squad, clubs(), roles()
    )
    assert len(outside.incoming_offers) == 1


def test_deadline_day_has_no_daily_limit():
    career = make_career()
    generate_incoming_offers(
        career, "2026-08-30", "2026-08-31", players(12), clubs(), roles()
    )
    assert len(career.incoming_offers) >= 3
    assert all(
        offer["created_at"] == "2026-08-31"
        for offer in career.incoming_offers
    )


def test_offer_expires_after_a_month():
    career = make_career()
    generate_incoming_offers(
        career, "2026-07-01", "2026-07-07", players(12), clubs(), roles()
    )
    offer = career.incoming_offers[0]
    career.date = offer["expires_at"]
    resolve_incoming_offers(career)
    assert offer["status"] == "expired"


def test_accept_inside_window_removes_player_and_pays_fee():
    career = make_career()
    generate_incoming_offers(
        career, "2026-07-01", "2026-07-07", players(12), clubs(), roles()
    )
    offer = career.incoming_offers[0]
    player_id = offer["player_id"]
    balance = career.balance
    accept_incoming_offer(career, offer["id"])
    assert offer["status"] == "accepted"
    assert offer["executed_at"] == career.date
    assert player_id not in career.player_ids
    assert career.balance == balance + offer["amount"]


def test_accept_outside_window_waits_for_the_window():
    career = make_career()
    career.date = "2026-09-15"
    career.incoming_offers.append(
        {
            "id": "offer-1",
            "player_id": "p0",
            "club_id": "domestic",
            "club_name": "Domestic FC",
            "club_logo": "",
            "club_country_id": ENGLAND,
            "club_country_name": "England",
            "club_league_name": "Championship",
            "kind": "transfer",
            "amount": 12_000_000,
            "loan_fee": 0,
            "wage_share": 0,
            "status": "pending",
            "created_at": career.date,
            "expires_at": "2026-10-15",
            "due": None,
            "responded_at": None,
            "counter_offers": 0,
            "counter": None,
            "acknowledged": False,
            "message": "Клуб ждёт вашего ответа.",
            "demand": {"amount": 15_000_000},
            "execute_on": None,
        }
    )
    accept_incoming_offer(career, "offer-1")
    assert "p0" in career.player_ids
    assert len(career.pending_departures) == 1
    assert career.balance == 0

    career.date = "2027-01-01"
    executed = execute_pending_departures(career)
    assert executed == ["p0"]
    assert "p0" not in career.player_ids
    assert career.balance == 12_000_000


def test_counter_gets_response_in_two_to_four_days_and_badge():
    career = make_career()
    career.date = "2026-07-05"
    career.incoming_offers.append(
        {
            "id": "offer-2",
            "player_id": "p0",
            "club_id": "domestic",
            "club_name": "Domestic FC",
            "club_logo": "",
            "club_country_id": ENGLAND,
            "club_country_name": "England",
            "club_league_name": "Championship",
            "kind": "transfer",
            "amount": 10_000_000,
            "loan_fee": 0,
            "wage_share": 0,
            "status": "pending",
            "created_at": career.date,
            "expires_at": "2026-08-04",
            "due": None,
            "responded_at": None,
            "counter_offers": 0,
            "counter": None,
            "acknowledged": False,
            "message": "Клуб ждёт вашего ответа.",
            "demand": {"amount": 14_000_000},
            "execute_on": None,
        }
    )
    counter_incoming_offer(career, "offer-2", 12_000_000)
    offer = career.incoming_offers[0]
    assert offer["status"] == "counter"
    delay = (date.fromisoformat(offer["due"]) - date.fromisoformat(career.date)).days
    assert 2 <= delay <= 4

    career.date = offer["due"]
    resolve_incoming_offers(career)
    assert offer["status"] == "accepted"
    assert offer["acknowledged"] is False
    assert offer["executed_at"] == career.date


def test_old_save_without_incoming_fields_loads(client: TestClient, saves_dir):
    import json

    career = create_api_career(client)
    path = saves_dir / f"{career['id']}.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw.pop("incoming_offers", None)
    raw.pop("pending_departures", None)
    raw.pop("incoming_market_date", None)
    path.write_text(json.dumps(raw), encoding="utf-8")

    response = client.get(f"/api/careers/{career['id']}")
    assert response.status_code == 200, response.text
    assert response.json()["transfers"]["received_offers"] == []
