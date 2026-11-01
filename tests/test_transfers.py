from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

ARSENAL = "11"
ENGLAND = "189"
HIDDEN_KEYS = {"overall", "pot", "market_value", "weekly_wage", "foot", "stats"}
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


def create_career(client: TestClient) -> dict:
    response = client.post(
        "/api/careers",
        json={
            "club_id": ARSENAL,
            "manager_name": "Transfer Tester",
            "manager_nationality_id": ENGLAND,
            "seed": 4242,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def search(client: TestClient, career_id: str, **params) -> dict:
    response = client.get(f"/api/careers/{career_id}/transfers/search", params=params)
    assert response.status_code == 200, response.text
    return response.json()


def test_empty_filter_returns_first_page_and_hides_scouted_values(client: TestClient):
    career = create_career(client)
    payload = search(client, career["id"])

    assert payload["total"] == 121927
    assert payload["limit"] == 40
    assert payload["offset"] == 0
    assert payload["has_more"] is True
    assert len(payload["items"]) == 40

    player = payload["items"][0]
    assert HIDDEN_KEYS.isdisjoint(player.keys())
    assert player["release_clause"] > 0
    assert player["photo"].startswith("/raster/players_faces")
    assert player["scouted"] is False


def test_offset_pages_do_not_repeat_and_report_has_more(client: TestClient):
    career = create_career(client)
    first = search(client, career["id"], limit=20)
    second = search(client, career["id"], limit=20, offset=20)

    first_ids = {player["id"] for player in first["items"]}
    second_ids = {player["id"] for player in second["items"]}
    assert not first_ids & second_ids
    assert second["has_more"] is True


def test_name_position_country_and_age_filters(client: TestClient):
    career = create_career(client)
    by_name = search(client, career["id"], name="David Raya", limit=100)
    assert any(player["name"] == "David Raya" for player in by_name["items"])

    keepers = search(
        client,
        career["id"],
        position="Goalkeeper",
        country_id=ENGLAND,
        age_min=20,
        age_max=24,
        limit=100,
    )
    assert keepers["total"] > 0
    for player in keepers["items"]:
        assert player["position"] == "Goalkeeper" or "Goalkeeper" in player["position_other"]
        assert player["country_id"] == ENGLAND
        assert 20 <= player["age"] <= 24


def test_league_club_foot_and_height_filters(client: TestClient):
    career = create_career(client)
    arsenal = search(client, career["id"], club_id=ARSENAL, limit=100)
    assert arsenal["total"] >= 20
    assert all(player["club_id"] == ARSENAL for player in arsenal["items"])

    tall_left = search(
        client,
        career["id"],
        league_id="GB1",
        foot="left",
        height_min=185,
        limit=100,
    )
    assert tall_left["total"] > 0
    for player in tall_left["items"]:
        assert player["league_id"] == "GB1"
        assert player["height"] >= 185


def test_free_agent_status_filter(client: TestClient):
    career = create_career(client)
    free_agents = search(client, career["id"], status="free", limit=100)
    assert free_agents["total"] == 1895
    assert all(player["club_id"] is None for player in free_agents["items"])
    assert all(player["status"] == "free" for player in free_agents["items"])


def test_sort_by_visible_and_hidden_fields(client: TestClient):
    career = create_career(client)
    by_age = search(client, career["id"], sort="age", direction="asc", limit=100)
    ages = [player["age"] for player in by_age["items"] if player["age"] is not None]
    assert ages == sorted(ages)

    by_name = search(client, career["id"], sort="name", direction="asc", limit=100)
    names = [player["name"].casefold() for player in by_name["items"]]
    assert names == sorted(names)

    by_position = search(client, career["id"], sort="position", direction="asc", limit=100)
    ranks = [ROLE_ORDER.get(player["role"], 99) for player in by_position["items"]]
    assert ranks == sorted(ranks)

    for sort in ("overall", "value", "wage"):
        payload = search(client, career["id"], sort=sort, direction="desc")
        assert payload["total"] == 121927
        assert HIDDEN_KEYS.isdisjoint(payload["items"][0].keys())


def test_unknown_career_returns_404(client: TestClient):
    response = client.get("/api/careers/does-not-exist/transfers/search")
    assert response.status_code == 404


def test_position_group_filter(client: TestClient):
    career = create_career(client)
    keepers = search(client, career["id"], group="GK", limit=100)
    assert keepers["total"] > 0
    assert all(player["role"] == "GK" for player in keepers["items"])

    forwards = search(client, career["id"], group="FWD", limit=100)
    assert forwards["total"] > 0
    assert all(player["role"] == "CF" for player in forwards["items"])


def test_external_contract_expiry_is_seeded_and_stable(client: TestClient):
    from datetime import date

    career = create_career(client)
    first = search(client, career["id"], limit=40)
    again = search(client, career["id"], limit=40)

    first_expiry = {player["id"]: player["contract_expires"] for player in first["items"]}
    again_expiry = {player["id"]: player["contract_expires"] for player in again["items"]}
    assert first_expiry == again_expiry
    assert any(value is not None for value in first_expiry.values())
    for value in first_expiry.values():
        if value is not None:
            expiry = date.fromisoformat(value)
            assert expiry > date.fromisoformat(career["date"])


def test_free_agents_have_no_contract_expiry(client: TestClient):
    career = create_career(client)
    free_agents = search(client, career["id"], status="free", limit=40)

    assert free_agents["items"]
    assert all(player["contract_expires"] is None for player in free_agents["items"])


def add_to_shortlist(client: TestClient, career_id: str, player_id: str) -> dict:
    response = client.post(
        f"/api/careers/{career_id}/actions",
        json={"type": "shortlist_add", "player_id": player_id},
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_shortlist_add_remove_toggle_and_idempotency(client: TestClient):
    career = create_career(client)
    player_id = "342229"

    added = add_to_shortlist(client, career["id"], player_id)
    assert [item["id"] for item in added["transfers"]["shortlist"]] == [player_id]
    assert added["transfers"]["shortlist"][0]["shortlisted"] is True

    again = add_to_shortlist(client, career["id"], player_id)
    assert [item["id"] for item in again["transfers"]["shortlist"]] == [player_id]

    toggled = client.post(
        f"/api/careers/{career['id']}/actions",
        json={"type": "shortlist_toggle", "player_id": player_id},
    )
    assert toggled.status_code == 200, toggled.text
    assert toggled.json()["transfers"]["shortlist"] == []

    toggled = client.post(
        f"/api/careers/{career['id']}/actions",
        json={"type": "shortlist_toggle", "player_id": player_id},
    )
    assert [item["id"] for item in toggled.json()["transfers"]["shortlist"]] == [player_id]

    removed = client.post(
        f"/api/careers/{career['id']}/actions",
        json={"type": "shortlist_remove", "player_id": player_id},
    )
    assert removed.status_code == 200, removed.text
    assert removed.json()["transfers"]["shortlist"] == []

    removed_again = client.post(
        f"/api/careers/{career['id']}/actions",
        json={"type": "shortlist_remove", "player_id": player_id},
    )
    assert removed_again.status_code == 200, removed_again.text
    assert removed_again.json()["transfers"]["shortlist"] == []


def test_shortlist_rejects_unknown_player(client: TestClient):
    career = create_career(client)
    for action_type in ("shortlist_add", "shortlist_remove", "shortlist_toggle"):
        response = client.post(
            f"/api/careers/{career['id']}/actions",
            json={"type": action_type, "player_id": "does-not-exist"},
        )
        assert response.status_code == 422, response.text
        assert response.json()["detail"] == "player not found"

    missing = client.post(
        f"/api/careers/{career['id']}/actions",
        json={"type": "shortlist_add"},
    )
    assert missing.status_code == 422


def test_search_marks_shortlisted_players(client: TestClient):
    career = create_career(client)
    add_to_shortlist(client, career["id"], "342229")

    payload = search(client, career["id"], name="Kylian Mbappé")
    assert payload["items"]
    assert payload["items"][0]["shortlisted"] is True

    others = search(client, career["id"], name="David Raya")
    assert others["items"]
    assert all(player["shortlisted"] is False for player in others["items"])


def test_shortlist_survives_reload_and_next_season(client: TestClient, saves_dir: Path):
    career = create_career(client)
    player_id = "342229"
    add_to_shortlist(client, career["id"], player_id)

    path = saves_dir / f"{career['id']}.json"
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["shortlist"] == [player_id]

    raw = saved
    raw["results"] = {fixture["id"]: {"home": 1, "away": 0} for fixture in raw["schedule"]}
    raw["date"] = "2027-03-01"
    path.write_text(json.dumps(raw), encoding="utf-8")

    loaded = client.get(f"/api/careers/{career['id']}")
    assert loaded.status_code == 200, loaded.text
    assert [item["id"] for item in loaded.json()["transfers"]["shortlist"]] == [player_id]

    response = client.post(
        f"/api/careers/{career['id']}/actions", json={"type": "next_season"}
    )
    assert response.status_code == 200, response.text
    started = response.json()
    assert started["season"]["season_start"] == "2027-07-01"
    assert [item["id"] for item in started["transfers"]["shortlist"]] == [player_id]

    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["shortlist"] == [player_id]


def test_transfer_centre_lists_shortlist_and_squad_statuses(client: TestClient):
    career = create_career(client)
    squad_id = career["squad"]["groups"][0]["players"][0]["id"]
    loan_id = career["squad"]["groups"][0]["players"][1]["id"]
    shortlist_id = "342229"

    for player_id, status in ((squad_id, "transfer"), (loan_id, "loan")):
        response = client.post(
            f"/api/careers/{career['id']}/actions",
            json={"type": "transfer_status", "player_id": player_id, "status": status},
        )
        assert response.status_code == 200, response.text

    updated = add_to_shortlist(client, career["id"], shortlist_id)
    transfers = updated["transfers"]

    assert [item["id"] for item in transfers["shortlist"]] == [shortlist_id]
    assert [item["id"] for item in transfers["listed"]] == [squad_id]
    assert [item["id"] for item in transfers["loaned"]] == [loan_id]
    assert transfers["sent_offers"] == []
    assert transfers["received_offers"] == []
    assert transfers["shortlist"][0]["scouting_state"] == "none"
    assert transfers["shortlist"][0]["negotiation_status"] is None
    assert HIDDEN_KEYS.isdisjoint(transfers["shortlist"][0].keys())
    assert transfers["listed"][0]["overall"] is not None

    scout = updated["scouting"]["scouts"][0]
    assigned = client.post(
        f"/api/careers/{career['id']}/actions",
        json={
            "type": "scout_assign",
            "scout_id": scout["id"],
            "player_id": shortlist_id,
        },
    )
    assert assigned.status_code == 200, assigned.text
    entry = assigned.json()["transfers"]["shortlist"][0]
    assert entry["scouting_state"] == "studying"
    assert entry["scouting_days_left"] >= 1
    assert entry["scouting_scout_name"] == scout["name"]


def test_old_save_without_shortlist_still_loads(client: TestClient, saves_dir: Path):
    career = create_career(client)
    path = saves_dir / f"{career['id']}.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw.pop("shortlist", None)
    path.write_text(json.dumps(raw), encoding="utf-8")

    loaded = client.get(f"/api/careers/{career['id']}")
    assert loaded.status_code == 200, loaded.text
    assert loaded.json()["transfers"]["shortlist"] == []
