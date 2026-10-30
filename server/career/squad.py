from __future__ import annotations

import random

from server.career.core import Career

SQUAD_ROLES = [
    {
        "id": "key",
        "label": "Ключевой игрок",
        "short": "Ключевой",
        "expected": 0.85,
    },
    {
        "id": "first",
        "label": "Основной игрок",
        "short": "Основной",
        "expected": 0.65,
    },
    {
        "id": "rotation",
        "label": "Игрок ротации",
        "short": "Ротация",
        "expected": 0.45,
    },
    {
        "id": "squad",
        "label": "Игрок резерва",
        "short": "Резерв",
        "expected": 0.25,
    },
    {
        "id": "prospect",
        "label": "Перспективный игрок",
        "short": "Перспектива",
        "expected": 0.10,
    },
]
ROLE_BY_ID = {role["id"]: role for role in SQUAD_ROLES}
DEFAULT_ROLE = "rotation"
ROLE_THRESHOLDS = (
    (0.11, "key"),
    (0.32, "first"),
    (0.57, "rotation"),
    (0.82, "squad"),
    (1.01, "prospect"),
)
MIN_MARKET_VALUE = 50_000


def expected_share(role_id: str | None) -> float:
    role = ROLE_BY_ID.get(str(role_id))
    return float(role["expected"]) if role else float(ROLE_BY_ID[DEFAULT_ROLE]["expected"])


def role_share(career: Career, player_id: str) -> float:
    contract = career.player_contracts.get(str(player_id)) or {}
    return expected_share(contract.get("squad_role"))


def morale_percent(actual_minutes: int, expected_minutes: int) -> int:
    if expected_minutes <= 0:
        return 100
    return max(0, min(100, round(actual_minutes / expected_minutes * 100)))


def _ranked(players: list[dict]) -> list[dict]:
    return sorted(
        players,
        key=lambda player: (
            -float(player.get("overall") or 0),
            str(player.get("name") or ""),
            str(player.get("id") or ""),
        ),
    )


def _role_for_rank(index: int, total: int) -> str:
    if total <= 0:
        return DEFAULT_ROLE
    position = index / total
    for threshold, role_id in ROLE_THRESHOLDS:
        if position < threshold:
            return role_id
    return "prospect"


def _rng(career: Career, player_id: str, salt: str) -> random.Random:
    return random.Random(f"{career.seed}:contract:{player_id}:{salt}")


def _round_money(value: float) -> int:
    if value >= 1_000_000:
        step = 100_000
    elif value >= 100_000:
        step = 10_000
    elif value >= 10_000:
        step = 1_000
    else:
        step = 100
    return max(step, int(round(value / step) * step))


def _contract_years(career: Career, player: dict, player_id: str) -> int:
    age = player.get("age")
    age = int(age) if isinstance(age, (int, float)) else 25
    if age <= 21:
        options = (4, 5)
    elif age <= 24:
        options = (3, 4, 5)
    elif age <= 27:
        options = (2, 3, 4)
    elif age <= 30:
        options = (2, 3)
    else:
        options = (1, 2)
    return _rng(career, player_id, "years").choice(options)


def _weekly_wage(career: Career, player: dict, player_id: str) -> int:
    value = max(int(player.get("market_value") or 0), MIN_MARKET_VALUE)
    age = player.get("age")
    age = int(age) if isinstance(age, (int, float)) else 25
    if age <= 23:
        age_factor = 1.1
    elif age <= 28:
        age_factor = 1.0
    elif age <= 31:
        age_factor = 0.9
    else:
        age_factor = 0.8
    jitter = _rng(career, player_id, "wage").uniform(0.9, 1.1)
    weekly = value * 0.12 * age_factor * jitter / 52
    return max(1_000, int(round(weekly / 100) * 100))


def _release_clause(career: Career, player: dict, player_id: str) -> int:
    value = max(int(player.get("market_value") or 0), MIN_MARKET_VALUE)
    multiplier = _rng(career, player_id, "clause").uniform(1.2, 2.0)
    return _round_money(value * multiplier)


def ensure_player_contracts(career: Career, players: list[dict]) -> None:
    ranked = _ranked(players)
    ranks = {str(player["id"]): index for index, player in enumerate(ranked)}
    total = len(ranked)
    for player in players:
        player_id = str(player["id"])
        contract = career.player_contracts.setdefault(player_id, {})
        if not ROLE_BY_ID.get(str(contract.get("squad_role"))):
            contract["squad_role"] = _role_for_rank(ranks[player_id], total)
        if not contract.get("years"):
            contract["years"] = _contract_years(career, player, player_id)
        if not contract.get("weekly_wage"):
            contract["weekly_wage"] = _weekly_wage(career, player, player_id)
        if not contract.get("release_clause"):
            contract["release_clause"] = _release_clause(career, player, player_id)


def contract_view(career: Career, player: dict, state: dict | None) -> dict:
    player_id = str(player["id"])
    contract = career.player_contracts.get(player_id) or {}
    role_id = str(contract.get("squad_role") or DEFAULT_ROLE)
    role = ROLE_BY_ID.get(role_id) or ROLE_BY_ID[DEFAULT_ROLE]
    stats = (state or {}).get("stats") or {}
    actual = int(stats.get("minutes") or 0)
    expected = int((state or {}).get("expected_minutes") or 0)
    return {
        "squad_role": role["id"],
        "squad_role_label": role["label"],
        "squad_role_short": role["short"],
        "expected_share": float(role["expected"]),
        "actual_minutes": actual,
        "expected_minutes": expected,
        "morale": morale_percent(actual, expected),
        "contract": {
            "years": int(contract.get("years") or 1),
            "weekly_wage": int(contract.get("weekly_wage") or 0),
            "release_clause": int(contract.get("release_clause") or 0),
        },
    }
