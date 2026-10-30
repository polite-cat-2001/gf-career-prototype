from __future__ import annotations

import random
from datetime import date, timedelta

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
MIN_SQUAD_SIZE = 11
MAX_SHIRT_NUMBER = 99
MIN_WEEKLY_WAGE = 1_000
MAX_WEEKLY_WAGE = 2_000_000
TRANSFER_STATUSES = ("transfer", "loan", "blocked")
MAX_COUNTER_OFFERS = 2
WAGE_COVER_WEEKS = 4
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
    return _wage_from_value(career, player_id, value, _player_age(player))


def _wage_from_value(career: Career, player_id: str, value: int, age: int) -> int:
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
    return max(MIN_WEEKLY_WAGE, int(round(weekly / 100) * 100))


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


def ensure_shirt_numbers(career: Career, players: list[dict]) -> None:
    ordered = sorted(players, key=lambda player: str(player["id"]))
    assigned: dict[str, int] = {}
    used: set[int] = set()
    for player in ordered:
        player_id = str(player["id"])
        number = career.shirt_numbers.get(player_id)
        if (
            isinstance(number, int)
            and 1 <= number <= MAX_SHIRT_NUMBER
            and number not in used
        ):
            assigned[player_id] = number
            used.add(number)
    for player in ordered:
        player_id = str(player["id"])
        if player_id in assigned:
            continue
        canon_number = player.get("shirt_number")
        if not isinstance(canon_number, (int, float)):
            continue
        number = int(canon_number)
        if 1 <= number <= MAX_SHIRT_NUMBER and number not in used:
            assigned[player_id] = number
            used.add(number)
    free = [number for number in range(1, MAX_SHIRT_NUMBER + 1) if number not in used]
    cursor = 0
    for player in ordered:
        player_id = str(player["id"])
        if player_id in assigned:
            continue
        if cursor >= len(free):
            break
        assigned[player_id] = free[cursor]
        cursor += 1
    career.shirt_numbers = assigned


def _clause_bounds(value: int) -> tuple[int, int]:
    return int(value * 1.2), int(value * 2.0)


def negotiation_demand(career: Career, player: dict, player_id: str) -> dict:
    value = max(
        int(career.player_values.get(player_id) or player.get("market_value") or 0),
        MIN_MARKET_VALUE,
    )
    age = _player_age(player)
    contract = career.player_contracts.get(player_id) or {}
    role_id = str(contract.get("squad_role") or DEFAULT_ROLE)
    share = expected_share(role_id)
    premium = 1.0 + (share - 0.45) * 0.6
    jitter = _rng(career, player_id, "renewal").uniform(0.97, 1.09)
    base = _wage_from_value(career, player_id, value, age) * premium * jitter
    wage = max(int(contract.get("weekly_wage") or 0), int(round(base / 100) * 100))
    if age <= 24:
        years = 4
    elif age <= 28:
        years = 3
    elif age <= 31:
        years = 2
    else:
        years = 1
    return {
        "years": years,
        "weekly_wage": min(MAX_WEEKLY_WAGE, max(MIN_WEEKLY_WAGE, wage)),
        "squad_role": role_id,
        "release_clause": _clause_bounds(value)[0],
    }


def _clean_terms(terms: dict) -> dict:
    years = int(terms.get("years") or 0)
    if not 1 <= years <= 5:
        raise ValueError("contract length must be between 1 and 5 years")
    wage = int(terms.get("weekly_wage") or 0)
    if not MIN_WEEKLY_WAGE <= wage <= MAX_WEEKLY_WAGE:
        raise ValueError("weekly wage is out of range")
    role_id = str(terms.get("squad_role") or "")
    if role_id not in ROLE_BY_ID:
        raise ValueError("unknown squad role")
    clause = int(terms.get("release_clause") or 0)
    if clause < 0:
        raise ValueError("release clause cannot be negative")
    return {
        "years": years,
        "weekly_wage": wage,
        "squad_role": role_id,
        "release_clause": clause,
    }


def _term_shortfalls(offer: dict, demand: dict, value: int) -> list[str]:
    shortfalls = []
    if int(offer["weekly_wage"]) < int(demand["weekly_wage"]):
        shortfalls.append("wage")
    if int(offer["years"]) < int(demand["years"]):
        shortfalls.append("years")
    if expected_share(offer["squad_role"]) < expected_share(demand["squad_role"]):
        shortfalls.append("role")
    minimum, maximum = _clause_bounds(value)
    if int(offer["release_clause"]) < minimum:
        shortfalls.append("clause_low")
    elif int(offer["release_clause"]) > maximum:
        shortfalls.append("clause_high")
    return shortfalls


def _counter_terms(offer: dict, demand: dict, value: int, shortfalls: list[str]) -> dict:
    minimum, maximum = _clause_bounds(value)
    clause = int(offer["release_clause"])
    if "clause_high" in shortfalls:
        clause = maximum
    else:
        clause = max(clause, minimum)
    return {
        "years": min(5, max(int(offer["years"]), int(demand["years"]))),
        "weekly_wage": max(int(offer["weekly_wage"]), int(demand["weekly_wage"])),
        "squad_role": demand["squad_role"] if "role" in shortfalls else offer["squad_role"],
        "release_clause": clause,
    }


COUNTER_MESSAGES = {
    "wage": "Игрок просит более высокую зарплату.",
    "years": "Игрок настаивает на более длительном контракте.",
    "role": "Игрок не готов потерять своё амплуа.",
    "clause_low": "Игрок хочет более высокие отступные.",
    "clause_high": "Отступные слишком высоки — игрок просит их снизить.",
}
ACCEPTED_MESSAGE = "Игрок согласен с условиями. Подтвердите подписание."
REFUSED_MESSAGE = "Игрок отказался от переговоров."
PENDING_MESSAGE = "Игрок обдумывает предложение."
THINK_DAYS = (2, 3, 4)


def _think_delay(career: Career, player_id: str, rounds: int) -> int:
    rng = random.Random(f"{career.seed}:thinking:{player_id}:{rounds}")
    return rng.choice(THINK_DAYS)


def start_negotiation(
    career: Career, player: dict, player_id: str, terms: dict
) -> dict:
    offer = _clean_terms(terms)
    state = career.negotiations.get(player_id)
    if state and state.get("status") == "accepted":
        raise ValueError("contract is already agreed, confirm it first")
    if state and state.get("status") == "pending":
        raise ValueError("the player is still thinking about the current offer")
    if not state or state.get("status") == "refused":
        state = {
            "demand": negotiation_demand(career, player, player_id),
            "counter_offers": 0,
            "rounds": 0,
            "status": "pending",
            "offer": None,
            "counter": None,
            "due": None,
            "acknowledged": True,
            "message": "",
        }
        career.negotiations[player_id] = state
    state["rounds"] = int(state.get("rounds") or 0) + 1
    delay = _think_delay(career, player_id, state["rounds"])
    state["due"] = (date.fromisoformat(career.date) + timedelta(days=delay)).isoformat()
    state["offer"] = offer
    state["counter"] = None
    state["status"] = "pending"
    state["acknowledged"] = True
    state["message"] = PENDING_MESSAGE
    return state


def _resolve_one(career: Career, player_id: str, state: dict) -> None:
    value = max(int(career.player_values.get(player_id) or 0), MIN_MARKET_VALUE)
    offer = _clean_terms(state.get("offer") or {})
    demand = state.get("demand") or {}
    shortfalls = _term_shortfalls(offer, demand, value)
    if not shortfalls:
        state["status"] = "accepted"
        state["counter"] = None
        state["message"] = ACCEPTED_MESSAGE
    elif int(state.get("counter_offers") or 0) >= MAX_COUNTER_OFFERS:
        state["status"] = "refused"
        state["counter"] = None
        state["message"] = REFUSED_MESSAGE
    else:
        state["counter_offers"] = int(state.get("counter_offers") or 0) + 1
        state["status"] = "counter"
        state["counter"] = _counter_terms(offer, demand, value, shortfalls)
        state["message"] = " ".join(
            COUNTER_MESSAGES[key] for key in shortfalls if key in COUNTER_MESSAGES
        )
    state["acknowledged"] = False


def resolve_negotiations(career: Career) -> None:
    for player_id, state in career.negotiations.items():
        if state.get("status") != "pending":
            continue
        due = state.get("due")
        if not due or career.date < due:
            continue
        try:
            _resolve_one(career, player_id, state)
        except ValueError:
            continue


def acknowledge_negotiation(career: Career, player_id: str) -> dict:
    state = career.negotiations.get(player_id)
    if not state:
        raise ValueError("there is no negotiation for this player")
    if state.get("status") == "pending":
        raise ValueError("the player is still thinking about the current offer")
    state["acknowledged"] = True
    return state


def accept_counter(career: Career, player_id: str) -> dict:
    state = career.negotiations.get(player_id)
    if not state or state.get("status") != "counter" or not state.get("counter"):
        raise ValueError("there is no counter-offer to accept")
    terms = _clean_terms(state["counter"])
    if not contract_affordable(career, player_id, terms["weekly_wage"]):
        raise ValueError("not enough money to accept these terms")
    contract = _apply_contract(career, player_id, terms)
    career.negotiations.pop(player_id, None)
    return contract


def contract_affordable(career: Career, player_id: str, weekly_wage: int) -> bool:
    if career.balance is None:
        return True
    total = sum(
        int((career.player_contracts.get(other_id) or {}).get("weekly_wage") or 0)
        for other_id in career.player_ids
    )
    current = int((career.player_contracts.get(player_id) or {}).get("weekly_wage") or 0)
    total = total - current + int(weekly_wage)
    return total * WAGE_COVER_WEEKS <= int(career.balance)


def _apply_contract(career: Career, player_id: str, terms: dict) -> dict:
    contract = career.player_contracts.setdefault(player_id, {})
    contract["years"] = int(terms["years"])
    contract["weekly_wage"] = int(terms["weekly_wage"])
    contract["squad_role"] = str(terms["squad_role"])
    contract["release_clause"] = int(terms["release_clause"])
    return contract


def sign_contract(career: Career, player_id: str) -> dict:
    state = career.negotiations.get(player_id)
    if not state or state.get("status") != "accepted":
        raise ValueError("the contract is not agreed yet")
    terms = _clean_terms(state.get("offer") or {})
    if not contract_affordable(career, player_id, terms["weekly_wage"]):
        raise ValueError("not enough money to sign this contract")
    contract = _apply_contract(career, player_id, terms)
    career.negotiations.pop(player_id, None)
    return contract


def contract_view(career: Career, player: dict, state: dict | None) -> dict:
    player_id = str(player["id"])
    contract = career.player_contracts.get(player_id) or {}
    role_id = str(contract.get("squad_role") or DEFAULT_ROLE)
    role = ROLE_BY_ID.get(role_id) or ROLE_BY_ID[DEFAULT_ROLE]
    stats = (state or {}).get("stats") or {}
    actual = int(stats.get("minutes") or 0)
    expected = int((state or {}).get("expected_minutes") or 0)
    negotiation = career.negotiations.get(player_id)
    if negotiation:
        terms = negotiation.get("counter") or negotiation.get("offer") or {}
        negotiation = {
            **negotiation,
            "affordable": contract_affordable(
                career, player_id, int(terms.get("weekly_wage") or 0)
            ),
        }
    return {
        "squad_role": role["id"],
        "squad_role_label": role["label"],
        "squad_role_short": role["short"],
        "expected_share": float(role["expected"]),
        "actual_minutes": actual,
        "expected_minutes": expected,
        "morale": morale_percent(actual, expected),
        "transfer_status": career.player_transfers.get(player_id),
        "negotiation": negotiation,
        "contract": {
            "years": int(contract.get("years") or 1),
            "weekly_wage": int(contract.get("weekly_wage") or 0),
            "release_clause": int(contract.get("release_clause") or 0),
        },
    }
