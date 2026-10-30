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
STARTING_BALANCE_RATIO = 0.25
STARTING_BALANCE_MIN = 1_000_000
VALUE_AGE_FACTORS = (
    (21, 1.15),
    (24, 1.08),
    (27, 1.02),
    (30, 0.94),
    (33, 0.84),
    (99, 0.68),
)


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
    rounded = _round_money(value * multiplier)
    return max(int(value * 1.2), min(int(value * 2.0), rounded))


def _player_age(player: dict) -> int:
    age = player.get("age")
    return int(age) if isinstance(age, (int, float)) else 25


def _age_value_factor(age: int) -> float:
    for max_age, factor in VALUE_AGE_FACTORS:
        if age <= max_age:
            return factor
    return VALUE_AGE_FACTORS[-1][1]


def _ovr_value_factor(overall) -> float:
    return max(0.8, min(1.25, 1 + (float(overall or 0) - 70) * 0.01))


def _minutes_value_factor(minutes: int, expected: int) -> float:
    if expected <= 0:
        return 1.0
    ratio = max(0.0, min(2.0, minutes / expected))
    return 0.85 + 0.15 * ratio


def _rolled_value(
    career: Career,
    player: dict,
    player_id: str,
    age: int,
) -> int:
    value = int(career.player_values.get(player_id) or player.get("market_value") or 0)
    value = max(MIN_MARKET_VALUE, value)
    state = career.player_state.get(player_id) or {}
    stats = state.get("stats") or {}
    minutes = int(stats.get("minutes") or 0)
    expected = int(state.get("expected_minutes") or 0)
    rolled = (
        value
        * _age_value_factor(age)
        * _ovr_value_factor(player.get("overall"))
        * _minutes_value_factor(minutes, expected)
    )
    return max(MIN_MARKET_VALUE, _round_money(rolled))


def ensure_player_finances(career: Career, players: list[dict]) -> None:
    for player in players:
        player_id = str(player["id"])
        value = int(career.player_values.get(player_id) or player.get("market_value") or 0)
        value = max(MIN_MARKET_VALUE, value)
        career.player_values[player_id] = value
        career.player_ages.setdefault(player_id, _player_age(player))
        player["market_value"] = value
        player["age"] = career.player_ages[player_id]
    if career.balance is None:
        total = sum(int(player.get("market_value") or 0) for player in players)
        career.balance = max(STARTING_BALANCE_MIN, _round_money(total * STARTING_BALANCE_RATIO))


def finance_view(career: Career, players: list[dict]) -> dict:
    total = sum(int(player.get("market_value") or 0) for player in players)
    weekly = sum(
        int((career.player_contracts.get(str(player["id"])) or {}).get("weekly_wage") or 0)
        for player in players
    )
    return {
        "balance": int(career.balance or 0),
        "total_market_value": total,
        "weekly_wage_bill": weekly,
    }


def rollover_player_values(career: Career, players: list[dict]) -> None:
    ensure_player_finances(career, players)
    for player in players:
        player_id = str(player["id"])
        age = int(career.player_ages.get(player_id) or _player_age(player)) + 1
        value = _rolled_value(career, player, player_id, age)
        career.player_values[player_id] = value
        career.player_ages[player_id] = age
        player["market_value"] = value
        player["age"] = age


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
