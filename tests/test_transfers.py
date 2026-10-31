from __future__ import annotations

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
