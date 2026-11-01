from __future__ import annotations

from datetime import date, timedelta

from fastapi.testclient import TestClient

ARSENAL = "11"
ENGLAND = "189"
SPAIN = "157"
MBAPPE = "342229"
HIDDEN_KEYS = {"overall", "pot", "market_value", "weekly_wage", "foot", "stats"}


def create_career(client: TestClient, seed: int = 4242) -> dict:
    response = client.post(
        "/api/careers",
        json={
            "club_id": ARSENAL,
            "manager_name": "Scout Tester",
            "manager_nationality_id": ENGLAND,
            "seed": seed,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def career_state(client: TestClient, career_id: str) -> dict:
    response = client.get(f"/api/careers/{career_id}")
    assert response.status_code == 200, response.text
    return response.json()


def action(client: TestClient, career_id: str, payload: dict) -> dict:
    response = client.post(f"/api/careers/{career_id}/actions", json=payload)
    assert response.status_code == 200, response.text
    return response.json()


def search(client: TestClient, career_id: str, **params) -> dict:
    response = client.get(f"/api/careers/{career_id}/transfers/search", params=params)
    assert response.status_code == 200, response.text
    return response.json()


def advance(client: TestClient, career_id: str, days: int) -> dict:
    current = date.fromisoformat(career_state(client, career_id)["date"])
    target = (current + timedelta(days=days)).isoformat()
    return action(client, career_id, {"type": "advance", "date": target})


def test_new_career_starts_with_two_scouts_and_six_slots(client: TestClient):
    career = create_career(client)
    scouting = career["scouting"]

    assert len(scouting["scouts"]) == 2
    assert scouting["max_scouts"] == 6
    assert len(scouting["candidates"]) == 5
    assert scouting["regions"]
    assert scouting["counts"] == {"new": 0, "updates": 0, "total": 0}
    for scout in scouting["scouts"]:
        assert 1 <= scout["experience"] <= 5
        assert 1 <= scout["judgement"] <= 5
        assert scout["flag"].startswith("/raster/country_flags")
        assert scout["task"] is None
        assert scout["report"] is None


def test_hire_scout_spends_budget_and_removes_candidate(client: TestClient):
    career = create_career(client)
    candidate = career["scouting"]["candidates"][0]
    balance = career["squad"]["finance"]["balance"]

    updated = action(
        client, career["id"], {"type": "scout_hire", "scout_id": candidate["id"]}
    )
    scouting = updated["scouting"]

    assert len(scouting["scouts"]) == 3
    assert candidate["id"] not in {item["id"] for item in scouting["candidates"]}
    assert updated["squad"]["finance"]["balance"] == balance - candidate["price"]


def test_player_report_locks_scout_and_player_then_reveals(client: TestClient):
    career = create_career(client)
    scout = career["scouting"]["scouts"][0]

    started = action(
        client,
        career["id"],
        {"type": "scout_assign", "scout_id": scout["id"], "player_id": MBAPPE},
    )
    report = started["scouting"]["scouts"][0]["report"]
    assert report["days_total"] == 6 - scout["experience"]
    assert report["days_left"] == report["days_total"]
    assert report["player_id"] == MBAPPE

    hidden = search(client, career["id"], name="Kylian Mbappé")["items"][0]
    assert hidden["scouted"] is False
    assert HIDDEN_KEYS.isdisjoint(hidden.keys())

    refused = client.post(
        f"/api/careers/{career['id']}/actions",
        json={
            "type": "scout_assign",
            "scout_id": scout["id"],
            "player_id": "418560",
        },
    )
    assert refused.status_code == 422
    assert "already studying" in refused.json()["detail"]

    other = career["scouting"]["scouts"][1]
    refused = client.post(
        f"/api/careers/{career['id']}/actions",
        json={
            "type": "scout_assign",
            "scout_id": other["id"],
            "player_id": MBAPPE,
        },
    )
    assert refused.status_code == 422

    ready = advance(client, career["id"], report["days_total"])
    assert ready["scouting"]["scouts"][0]["report"] is None
    reports = ready["scouting"]["reports"]
    assert len(reports) == 1
    assert reports[0]["kind"] == "report"
    assert reports[0]["player"]["id"] == MBAPPE
    assert reports[0]["acknowledged"] is False
    assert ready["scouting"]["counts"]["new"] == 1

    revealed = search(client, career["id"], name="Kylian Mbappé")["items"][0]
    assert revealed["scouted"] is True
    assert revealed["overall"] > 80
    assert revealed["weekly_wage"] > 0
    assert revealed["foot"]
    assert isinstance(revealed["stats"], dict) and revealed["stats"]


def test_network_finds_recommendations_and_task_can_be_edited(client: TestClient):
    career = create_career(client)
    scout = career["scouting"]["scouts"][1]

    started = action(
        client,
        career["id"],
        {
            "type": "scout_network",
            "scout_id": scout["id"],
            "region_id": "south-europe",
            "country_id": SPAIN,
        },
    )
    task = started["scouting"]["scouts"][1]["task"]
    assert task["country_id"] == SPAIN
    assert task["days_worked"] == 0
    assert task["found_count"] == 0
    assert started["scouting"]["networks"][0]["country_id"] == SPAIN

    found = advance(client, career["id"], 1)["scouting"]
    assert found["scouts"][1]["task"]["days_worked"] == 1
    assert found["scouts"][1]["task"]["found_count"] > 0
    assert found["recommendations"]
    recommendation = found["recommendations"][0]
    assert recommendation["kind"] == "recommendation"
    assert recommendation["player"]["scouted"] is True

    revealed = search(
        client, career["id"], name=recommendation["player"]["name"], limit=5
    )["items"]
    revealed_ids = {player["id"] for player in revealed if player["scouted"]}
    assert recommendation["player"]["id"] in revealed_ids

    updated = action(
        client,
        career["id"],
        {
            "type": "scout_task",
            "scout_id": scout["id"],
            "criteria": {"role": "GK", "age_min": 20, "age_max": 30},
        },
    )
    criteria = updated["scouting"]["scouts"][1]["task"]["criteria"]
    assert criteria == {
        "role": "GK",
        "age_min": 20,
        "age_max": 30,
        "contract_min": None,
        "contract_max": None,
    }


def test_remove_recommendation_and_acknowledge_reports(client: TestClient):
    career = create_career(client)
    scout = career["scouting"]["scouts"][1]
    action(
        client,
        career["id"],
        {
            "type": "scout_network",
            "scout_id": scout["id"],
            "region_id": "south-europe",
            "country_id": SPAIN,
        },
    )
    found = advance(client, career["id"], 1)["scouting"]
    player_id = found["recommendations"][0]["player"]["id"]
    assert found["counts"]["new"] > 0

    acknowledged = action(client, career["id"], {"type": "scout_ack"})
    assert acknowledged["scouting"]["counts"]["new"] == 0

    removed = action(
        client, career["id"], {"type": "scout_remove", "player_id": player_id}
    )
    assert player_id not in {
        item["player"]["id"] for item in removed["scouting"]["recommendations"]
    }
    assert removed["scouting"]["scouts"][1]["task"]["found_count"] >= 0

    hidden = search(client, career["id"], name="", limit=100)["items"]
    assert all(
        player["scouted"] is False for player in hidden if player["id"] == player_id
    )


def test_network_task_and_report_coexist_and_report_can_be_reassigned(client: TestClient):
    career = create_career(client)
    scout = career["scouting"]["scouts"][0]

    action(
        client,
        career["id"],
        {
            "type": "scout_network",
            "scout_id": scout["id"],
            "region_id": "south-europe",
            "country_id": SPAIN,
        },
    )
    started = action(
        client,
        career["id"],
        {"type": "scout_assign", "scout_id": scout["id"], "player_id": MBAPPE},
    )
    report = started["scouting"]["scouts"][0]["report"]
    assert report["player_id"] == MBAPPE
    assert started["scouting"]["scouts"][0]["task"] is not None

    refused = client.post(
        f"/api/careers/{career['id']}/actions",
        json={
            "type": "scout_assign",
            "scout_id": scout["id"],
            "player_id": "418560",
        },
    )
    assert refused.status_code == 422

    ready = advance(client, career["id"], report["days_total"])
    assert ready["scouting"]["scouts"][0]["report"] is None

    reassigned = action(
        client,
        career["id"],
        {"type": "scout_assign", "scout_id": scout["id"], "player_id": "418560"},
    )
    reassigned_report = reassigned["scouting"]["scouts"][0]["report"]
    assert reassigned_report is not None
    assert reassigned_report["player_id"] == "418560"
