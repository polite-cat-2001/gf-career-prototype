from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

ARSENAL = "11"
ENGLAND = "189"


def create_career(client: TestClient, name: str = "Ada Lovelace", seed: int | None = 4242) -> dict:
    payload = {
        "club_id": ARSENAL,
        "manager_name": name,
        "manager_nationality_id": ENGLAND,
    }
    if seed is not None:
        payload["seed"] = seed
    response = client.post("/api/careers", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_create_returns_full_snapshot(client: TestClient):
    snapshot = create_career(client)

    assert snapshot["version"] == 1
    assert snapshot["seed"] == 4242
    assert snapshot["date"] == "2026-07-01"
    assert snapshot["manager"] == {
        "name": "Ada Lovelace",
        "nationality_id": ENGLAND,
        "nationality": "England",
    }
    assert snapshot["club"]["id"] == ARSENAL
    assert snapshot["club"]["name"] == "Arsenal FC"
    assert snapshot["club"]["league_name"] == "Premier League"
    assert snapshot["club"]["stadium"]["name"]

    squad = snapshot["squad"]
    assert squad["summary"]["squad_size"] >= 20
    assert squad["summary"]["average_overall"] > 0
    assert squad["summary"]["average_age"] > 0
    assert squad["summary"]["total_market_value"] > 0
    assert squad["groups"]
    assert squad["groups"][0]["role"] == "GK"
    assert squad["groups"][0]["players"]
    assert sum(len(group["players"]) for group in squad["groups"]) == squad["summary"]["squad_size"]
    assert all("stats" not in player for group in squad["groups"] for player in group["players"])

    lineup = squad["lineup"]
    assert lineup["formation"] == "4-3-3"
    assert len(lineup["slots"]) == 11
    starters = [slot["player"]["id"] for slot in lineup["slots"]]
    assert len(set(starters)) == 11
    assert lineup["slots"][0]["role"] == "GK"
    assert lineup["slots"][0]["player"]["role"] == "GK"
    assert all(slot["player"]["fatigue"] == 100 for slot in lineup["slots"])
    bench_ids = [player["id"] for player in lineup["bench"]]
    assert not set(bench_ids) & set(starters)
    assert len(bench_ids) == squad["summary"]["squad_size"] - 11
    assert all("stats" not in player for player in lineup["bench"])


def test_create_generates_random_seed_when_omitted(client: TestClient):
    first = create_career(client, name="First", seed=None)
    second = create_career(client, name="Second", seed=None)
    assert first["seed"] != second["seed"]


def test_save_then_load_matches_snapshot(client: TestClient):
    created = create_career(client)
    saved = client.post(f"/api/careers/{created['id']}/save")
    assert saved.status_code == 200, saved.text

    loaded = client.get(f"/api/careers/{created['id']}")
    assert loaded.status_code == 200, loaded.text
    assert loaded.json() == saved.json()


def test_list_and_latest_use_last_modified_save(client: TestClient):
    first = create_career(client, name="First")
    second = create_career(client, name="Second")

    listed = client.get("/api/careers")
    assert listed.status_code == 200
    ids = [item["id"] for item in listed.json()]
    assert ids[0] == second["id"]
    assert ids[1] == first["id"]
    assert listed.json()[0]["club_name"] == "Arsenal FC"

    client.post(f"/api/careers/{first['id']}/save")
    latest = client.get("/api/careers/latest")
    assert latest.status_code == 200
    assert latest.json()["id"] == first["id"]


def test_unknown_career_returns_404(client: TestClient):
    assert client.get("/api/careers/does-not-exist").status_code == 404
    assert client.get("/api/careers/latest").status_code == 404


def test_version_mismatch_is_a_clear_refusal(client: TestClient, saves_dir: Path):
    career_id = "0123456789abcdef0123456789abcdef"
    saves_dir.mkdir(parents=True, exist_ok=True)
    (saves_dir / f"{career_id}.json").write_text(
        json.dumps({"version": 999, "id": career_id}),
        encoding="utf-8",
    )

    response = client.get(f"/api/careers/{career_id}")
    assert response.status_code == 409
    detail = response.json()["detail"]
    assert "version 999" in detail
    assert "requires version 1" in detail
    assert "Migrations are not available" in detail

    listed = client.get("/api/careers")
    assert listed.status_code == 200
    item = listed.json()[0]
    assert item["id"] == career_id
    assert item["compatible"] is False
    assert "version 999" in item["problem"]


def test_create_rejects_unknown_club_and_nationality(client: TestClient):
    response = client.post(
        "/api/careers",
        json={
            "club_id": "does-not-exist",
            "manager_name": "Ada Lovelace",
            "manager_nationality_id": ENGLAND,
        },
    )
    assert response.status_code == 404

    response = client.post(
        "/api/careers",
        json={
            "club_id": ARSENAL,
            "manager_name": "Ada Lovelace",
            "manager_nationality_id": "does-not-exist",
        },
    )
    assert response.status_code == 404


def test_create_rejects_blank_manager_name(client: TestClient):
    response = client.post(
        "/api/careers",
        json={
            "club_id": ARSENAL,
            "manager_name": "   ",
            "manager_nationality_id": ENGLAND,
        },
    )
    assert response.status_code == 422
