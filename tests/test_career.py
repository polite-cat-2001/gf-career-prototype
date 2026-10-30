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


def advance_to_match(client: TestClient, snapshot: dict) -> dict:
    response = client.post(
        f"/api/careers/{snapshot['id']}/actions",
        json={"type": "advance", "date": snapshot["season"]["next"]["date"]},
    )
    assert response.status_code == 200, response.text
    return response.json()


def play_match(client: TestClient, snapshot: dict) -> dict:
    advance_to_match(client, snapshot)
    response = client.post(f"/api/careers/{snapshot['id']}/actions", json={"type": "play"})
    assert response.status_code == 200, response.text
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
    assert all(
        len(player["stats"]) == 22 for group in squad["groups"] for player in group["players"]
    )

    lineup = squad["lineup"]
    assert lineup["formation"] == "4-3-3"
    assert len(lineup["slots"]) == 11
    starters = [slot["player"]["id"] for slot in lineup["slots"]]
    assert len(set(starters)) == 11
    assert lineup["slots"][0]["role"] == "GK"
    assert lineup["slots"][0]["player"]["role"] == "GK"
    assert all(slot["player"]["fatigue"] == 100 for slot in lineup["slots"])
    bench_ids = [player["id"] for player in lineup["bench"]]
    reserve_ids = [player["id"] for player in lineup["reserve"]]
    assert not set(bench_ids + reserve_ids) & set(starters)
    assert len(bench_ids) <= 7
    assert len(bench_ids) + len(reserve_ids) == squad["summary"]["squad_size"] - 11
    assert all(len(slot["player"]["stats"]) == 22 for slot in lineup["slots"])
    assert all(len(player["stats"]) == 22 for player in lineup["bench"])
    assert all(len(player["stats"]) == 22 for player in lineup["reserve"])


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


def test_create_builds_league_schedule(client: TestClient):
    snapshot = create_career(client)
    season = snapshot["season"]

    assert season["season_start"] == "2026-07-01"
    assert season["round"] == 1
    assert season["rounds_total"] == 38
    assert season["complete"] is False
    assert season["last_result"] is None
    assert season["form"] == []
    assert season["next"]["round"] == 1
    assert season["next"]["date"] == "2026-07-08"
    assert season["next"]["opponent"]["id"] != ARSENAL
    assert season["next"]["opponent"]["strength"] > 0
    assert len(season["standings"]) == 20
    assert all(row["played"] == 0 and row["points"] == 0 for row in season["standings"])


def test_play_round_simulates_results_and_updates_table(client: TestClient, saves_dir: Path):
    created = create_career(client)
    played = play_match(client, created)
    season = played["season"]

    result = season["last_result"]
    assert result["round"] == 1
    assert result["outcome"] in {"W", "D", "L"}
    assert season["form"] == [result]
    assert season["next"]["round"] == 2
    assert season["round"] == 2
    assert played["date"] == "2026-07-09"

    standings = season["standings"]
    assert sum(row["played"] for row in standings) == 20
    assert sum(row["won"] for row in standings) == sum(row["lost"] for row in standings)
    assert sum(row["points"] for row in standings) == 3 * sum(row["won"] for row in standings) + sum(
        row["drawn"] for row in standings
    )
    own = next(row for row in standings if row["club_id"] == ARSENAL)
    assert own["played"] == 1

    raw = json.loads((saves_dir / f"{created['id']}.json").read_text(encoding="utf-8"))
    assert len(raw["schedule"]) == 380
    assert len(raw["results"]) == 10
    assert raw["date"] == "2026-07-09"
    assert raw["journal"][-1]["type"] == "match.played"
    assert raw["journal"][-1]["payload"]["fixture_id"] == result["fixture_id"]
    assert raw["results"][result["fixture_id"]]["home"] == (
        result["goals_for"] if result["home"] else result["goals_against"]
    )

    loaded = client.get(f"/api/careers/{created['id']}")
    assert loaded.status_code == 200
    assert loaded.json()["season"] == season


def test_same_seed_replays_the_same_round(client: TestClient):
    first = create_career(client, name="First", seed=777)
    second = create_career(client, name="Second", seed=777)
    for snapshot in (first, second):
        snapshot["played"] = play_match(client, snapshot)["season"]

    assert first["played"]["last_result"] == second["played"]["last_result"]
    assert first["played"]["standings"] == second["played"]["standings"]


def test_play_uses_schedule_even_for_saves_without_one(client: TestClient, saves_dir: Path):
    created = create_career(client)
    path = saves_dir / f"{created['id']}.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw.pop("schedule")
    raw.pop("results", None)
    path.write_text(json.dumps(raw), encoding="utf-8")

    loaded = client.get(f"/api/careers/{created['id']}")
    assert loaded.status_code == 200, loaded.text
    assert loaded.json()["season"]["round"] == 1

    advance_to_match(client, loaded.json())
    response = client.post(f"/api/careers/{created['id']}/actions", json={"type": "play"})
    assert response.status_code == 200, response.text
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert len(saved["schedule"]) == 380
    assert len(saved["results"]) == 10


def test_swap_then_play_keeps_the_new_lineup(client: TestClient):
    created = create_career(client)
    lineup = created["squad"]["lineup"]
    bench_player = lineup["bench"][0]
    starter = lineup["slots"][5]["player"]
    client.post(
        f"/api/careers/{created['id']}/actions",
        json={"type": "swap", "player_a": starter["id"], "player_b": bench_player["id"]},
    )

    response = play_match(client, created)
    updated = response["squad"]["lineup"]
    assert updated["slots"][5]["player"]["id"] == bench_player["id"]


def test_advance_moves_day_by_day_and_stops_at_match_day(client: TestClient):
    created = create_career(client)
    career_id = created["id"]
    assert created["date"] == "2026-07-01"

    stopped = client.post(
        f"/api/careers/{career_id}/actions",
        json={"type": "advance", "date": "2026-07-04"},
    )
    assert stopped.status_code == 200, stopped.text
    assert stopped.json()["date"] == "2026-07-04"
    assert stopped.json()["season"]["next"]["date"] == "2026-07-08"

    backwards = client.post(
        f"/api/careers/{career_id}/actions",
        json={"type": "advance", "date": "2026-07-02"},
    )
    assert backwards.status_code == 422

    skipped = client.post(
        f"/api/careers/{career_id}/actions",
        json={"type": "advance", "date": "2026-07-09"},
    )
    assert skipped.status_code == 422

    too_early = client.post(f"/api/careers/{career_id}/actions", json={"type": "play"})
    assert too_early.status_code == 422

    at_match = client.post(
        f"/api/careers/{career_id}/actions",
        json={"type": "advance", "date": "2026-07-08"},
    )
    assert at_match.status_code == 200
    played = client.post(f"/api/careers/{career_id}/actions", json={"type": "play"})
    assert played.status_code == 200, played.text
    assert played.json()["date"] == "2026-07-09"


def test_next_season_resets_results_and_moves_calendar(client: TestClient, saves_dir: Path):
    created = create_career(client)
    path = saves_dir / f"{created['id']}.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["results"] = {fixture["id"]: {"home": 1, "away": 0} for fixture in raw["schedule"]}
    raw["date"] = "2027-03-01"
    path.write_text(json.dumps(raw), encoding="utf-8")

    loaded = client.get(f"/api/careers/{created['id']}")
    assert loaded.status_code == 200, loaded.text
    season = loaded.json()["season"]
    assert season["complete"] is True
    assert season["next"] is None

    response = client.post(
        f"/api/careers/{created['id']}/actions", json={"type": "next_season"}
    )
    assert response.status_code == 200, response.text
    started = response.json()
    assert started["date"] == "2027-07-01"
    assert started["season"]["season_start"] == "2027-07-01"
    assert started["season"]["round"] == 1
    assert started["season"]["complete"] is False
    assert started["season"]["next"]["date"] == "2027-07-08"
    assert all(row["played"] == 0 and row["points"] == 0 for row in started["season"]["standings"])

    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved.get("results", {}) == {}
    assert saved["season_start"] == "2027-07-01"
    assert saved["schedule"][0]["date"] == "2027-07-08"
    assert [entry["type"] for entry in saved["journal"][-2:]] == [
        "season.completed",
        "season.started",
    ]


def test_old_schedule_gets_balanced_home_and_away(client: TestClient, saves_dir: Path):
    created = create_career(client)
    path = saves_dir / f"{created['id']}.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw.pop("schedule_version")
    for fixture in raw["schedule"]:
        if ARSENAL in (fixture["home"], fixture["away"]):
            opponent = fixture["away"] if fixture["home"] == ARSENAL else fixture["home"]
            fixture["home"] = ARSENAL
            fixture["away"] = opponent
    path.write_text(json.dumps(raw), encoding="utf-8")

    loaded = client.get(f"/api/careers/{created['id']}")
    assert loaded.status_code == 200, loaded.text
    next_date = loaded.json()["season"]["next"]["date"]
    response = client.post(
        f"/api/careers/{created['id']}/actions",
        json={"type": "advance", "date": next_date},
    )
    assert response.status_code == 200, response.text

    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["schedule_version"] == 2
    home = sum(1 for fixture in saved["schedule"] if fixture["home"] == ARSENAL)
    away = sum(1 for fixture in saved["schedule"] if fixture["away"] == ARSENAL)
    assert home == away == 19


def test_next_season_is_refused_until_the_season_is_complete(client: TestClient):
    created = create_career(client)
    response = client.post(
        f"/api/careers/{created['id']}/actions", json={"type": "next_season"}
    )
    assert response.status_code == 422


def test_swap_starters_exchanges_slots_and_persists(client: TestClient, saves_dir: Path):
    created = create_career(client)
    slots = created["squad"]["lineup"]["slots"]
    first = slots[0]["player"]
    second = slots[9]["player"]

    response = client.post(
        f"/api/careers/{created['id']}/actions",
        json={"type": "swap", "player_a": first["id"], "player_b": second["id"]},
    )
    assert response.status_code == 200, response.text
    swapped = response.json()
    assert swapped["squad"]["lineup"]["slots"][0]["player"]["id"] == second["id"]
    assert swapped["squad"]["lineup"]["slots"][9]["player"]["id"] == first["id"]

    loaded = client.get(f"/api/careers/{created['id']}")
    assert loaded.json()["squad"]["lineup"] == swapped["squad"]["lineup"]
    raw = json.loads((saves_dir / f"{created['id']}.json").read_text(encoding="utf-8"))
    assert raw["lineup"] == [slot["player"]["id"] for slot in swapped["squad"]["lineup"]["slots"]]
    assert raw["journal"][-1]["type"] == "lineup.swap"


def test_swap_starter_with_bench_moves_both(client: TestClient):
    created = create_career(client)
    lineup = created["squad"]["lineup"]
    starter = lineup["slots"][5]["player"]
    sub = lineup["bench"][0]

    response = client.post(
        f"/api/careers/{created['id']}/actions",
        json={"type": "swap", "player_a": starter["id"], "player_b": sub["id"]},
    )
    assert response.status_code == 200, response.text
    swapped = response.json()["squad"]["lineup"]
    assert swapped["slots"][5]["player"]["id"] == sub["id"]
    assert starter["id"] in [player["id"] for player in swapped["bench"]]


def test_swap_bench_pair_reorders_bench_and_persists(client: TestClient, saves_dir: Path):
    created = create_career(client)
    bench = created["squad"]["lineup"]["bench"]
    first, second = bench[0], bench[1]

    response = client.post(
        f"/api/careers/{created['id']}/actions",
        json={"type": "swap", "player_a": first["id"], "player_b": second["id"]},
    )
    assert response.status_code == 200, response.text
    swapped = response.json()["squad"]["lineup"]
    assert [player["id"] for player in swapped["bench"][:2]] == [second["id"], first["id"]]

    loaded = client.get(f"/api/careers/{created['id']}")
    assert [player["id"] for player in loaded.json()["squad"]["lineup"]["bench"][:2]] == [
        second["id"],
        first["id"],
    ]

    raw = json.loads((saves_dir / f"{created['id']}.json").read_text(encoding="utf-8"))
    assert raw["bench"][:2] == [second["id"], first["id"]]
    assert raw["journal"][-1]["type"] == "lineup.swap"


def test_swap_rejects_unknown_player_and_same_player(client: TestClient):
    created = create_career(client)
    starter = created["squad"]["lineup"]["slots"][1]["player"]

    unknown = client.post(
        f"/api/careers/{created['id']}/actions",
        json={"type": "swap", "player_a": starter["id"], "player_b": "does-not-exist"},
    )
    assert unknown.status_code == 422

    same = client.post(
        f"/api/careers/{created['id']}/actions",
        json={"type": "swap", "player_a": starter["id"], "player_b": starter["id"]},
    )
    assert same.status_code == 422

    unknown_action = client.post(
        f"/api/careers/{created['id']}/actions", json={"type": "train"}
    )
    assert unknown_action.status_code == 422
