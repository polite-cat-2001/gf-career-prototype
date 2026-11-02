from __future__ import annotations

import random
from datetime import date, timedelta

from server.career.core import Career
from server.career.squad import (
    DEFAULT_ROLE,
    MAX_COUNTER_OFFERS,
    MAX_WEEKLY_WAGE,
    MIN_MARKET_VALUE,
    MIN_WEEKLY_WAGE,
    ROLE_BY_ID,
    ROLE_THRESHOLDS,
    contract_expiry_for,
    contract_months_for,
    expected_share,
    weekly_wage_for,
)
from server.career.transfers import find_offer

THINK_DAYS = (2, 3, 4)
FREE_AGENT_MONTHS = 6
PENDING_MESSAGE = "Игрок обдумывает контракт."
ACCEPTED_MESSAGE = "Игрок согласен с условиями. Подтвердите подписание."
REFUSED_MESSAGE = "Игрок отказался от переговоров."
COUNTER_MESSAGES = {
    "wage": "Игрок просит более высокую зарплату.",
    "years": "Игрок настаивает на более длительном контракте.",
    "role": "Игрок не готов потерять своё амплуа.",
    "clause_low": "Игрок хочет более высокие отступные.",
    "clause_high": "Отступные слишком высоки — игрок просит их снизить.",
}


def transfer_window_open(value: str) -> bool:
    current = date.fromisoformat(str(value)[:10])
    return current.month == 1 or current.month in (7, 8)


def next_transfer_window(value: str) -> str:
    current = date.fromisoformat(str(value)[:10])
    if current.month <= 6:
        return date(current.year, 7, 1).isoformat()
    return date(current.year + 1, 1, 1).isoformat()


def _execution_date(value: str) -> str:
    if transfer_window_open(value):
        return str(value)[:10]
    return next_transfer_window(value)


def _player_value(career: Career, player: dict) -> int:
    player_id = str(player["id"])
    return max(
        int(career.player_values.get(player_id) or player.get("market_value") or 0),
        MIN_MARKET_VALUE,
    )


def _player_age(player: dict) -> int:
    age = player.get("age")
    return int(age) if isinstance(age, (int, float)) else 25


def _clause_bounds(value: int) -> tuple[int, int]:
    return int(value * 1.2), int(value * 2.0)


def projected_role(player: dict, squad_players: list[dict] | None) -> str:
    squad = list(squad_players or [])
    if not squad:
        return DEFAULT_ROLE
    overall = float(player.get("overall") or 0)
    better = sum(
        1
        for other in squad
        if str(other.get("id")) != str(player.get("id"))
        and (
            float(other.get("overall") or 0) > overall
            or (
                float(other.get("overall") or 0) == overall
                and str(other.get("name") or "") < str(player.get("name") or "")
            )
        )
    )
    position = better / (len(squad) + 1)
    for threshold, role_id in ROLE_THRESHOLDS:
        if position < threshold:
            return role_id
    return "prospect"


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


def transfer_contract_demand(
    career: Career, player: dict, squad_players: list[dict] | None = None
) -> dict:
    player_id = str(player["id"])
    value = _player_value(career, player)
    age = _player_age(player)
    role_id = projected_role(player, squad_players)
    share = expected_share(role_id)
    premium = 1.0 + (share - 0.45) * 0.6
    rng = random.Random(f"{career.seed}:transfer-contract:{player_id}:demand")
    base = weekly_wage_for(career, player, player_id) * premium * rng.uniform(0.97, 1.09)
    wage = int(round(base / 100) * 100)
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


def transfer_contract_defaults(
    career: Career, player: dict, squad_players: list[dict] | None = None
) -> dict:
    player_id = str(player["id"])
    value = _player_value(career, player)
    months = contract_months_for(career, player, player_id)
    if months > 0:
        years = max(1, min(5, int(round(months / 12))))
    else:
        years = 3
    return {
        "years": years,
        "weekly_wage": weekly_wage_for(career, player, player_id),
        "squad_role": projected_role(player, squad_players),
        "release_clause": _clause_bounds(value)[0],
    }


def _think_delay(career: Career, player_id: str, rounds: int) -> int:
    rng = random.Random(f"{career.seed}:transfer-thinking:{player_id}:{rounds}")
    return rng.choice(THINK_DAYS)


def _has_pending_transfer(career: Career, player_id: str) -> bool:
    return any(
        str(item.get("player_id")) == str(player_id)
        for item in career.pending_transfers
    )


def can_discuss_contract(career: Career, player: dict) -> bool:
    player_id = str(player["id"])
    if player_id in career.player_ids:
        return False
    if _has_pending_transfer(career, player_id):
        return False
    if not player.get("club_id"):
        return True
    expiry = contract_expiry_for(career, player, player_id)
    if not expiry:
        return True
    remaining = date.fromisoformat(expiry) - date.fromisoformat(career.date)
    return remaining.days <= FREE_AGENT_MONTHS * 31


def _offer_terms(career: Career, offer: dict | None) -> dict:
    if offer is None:
        return {
            "kind": "free",
            "fee": 0,
            "loan_fee": 0,
            "wage_share": 100,
            "offer_id": None,
            "offer": None,
        }
    status = str(offer.get("status"))
    if status != "accepted":
        raise ValueError("the club has not accepted an offer for this player")
    if offer.get("signed"):
        raise ValueError("this transfer has already been completed")
    kind = str(offer.get("kind") or "transfer")
    if kind == "loan":
        fee = int(offer.get("loan_fee") or offer.get("amount") or 0)
        return {
            "kind": "loan",
            "fee": fee,
            "loan_fee": fee,
            "wage_share": int(offer.get("wage_share") or 100),
            "offer_id": str(offer.get("id") or ""),
            "offer": offer,
        }
    return {
        "kind": "transfer",
        "fee": int(offer.get("amount") or 0),
        "loan_fee": 0,
        "wage_share": 100,
        "offer_id": str(offer.get("id") or ""),
        "offer": offer,
    }


def start_transfer_contract(
    career: Career,
    player: dict,
    terms: dict,
    *,
    offer: dict | None = None,
    squad_players: list[dict] | None = None,
) -> dict:
    player_id = str(player["id"])
    if player_id in career.player_ids:
        raise ValueError("the player is already in your squad")
    if _has_pending_transfer(career, player_id):
        raise ValueError("this transfer is already agreed and waiting for the window")
    if offer is None and not can_discuss_contract(career, player):
        raise ValueError(
            "contract talks are only available for free agents or expiring contracts"
        )
    context = _offer_terms(career, offer)
    clean = _clean_terms(terms)

    state = career.transfer_contracts.get(player_id)
    if state and state.get("status") == "accepted":
        raise ValueError("the contract is already agreed, confirm it first")
    if state and state.get("status") == "pending":
        raise ValueError("the player is still thinking about the current offer")
    if not state or state.get("status") == "refused":
        state = {
            "player_id": player_id,
            "overall": round(float(player.get("overall") or 0), 1),
            "value": _player_value(career, player),
            "demand": transfer_contract_demand(career, player, squad_players),
            "counter_offers": 0,
            "rounds": 0,
            "status": "pending",
            "offer": None,
            "counter": None,
            "agreed": None,
            "due": None,
            "message": "",
        }
        career.transfer_contracts[player_id] = state

    state.update(
        {
            "overall": round(float(player.get("overall") or 0), 1),
            "offer_id": context["offer_id"],
            "kind": context["kind"],
            "fee": context["fee"],
            "loan_fee": context["loan_fee"],
            "wage_share": context["wage_share"],
        }
    )
    state["rounds"] = int(state.get("rounds") or 0) + 1
    delay = _think_delay(career, player_id, state["rounds"])
    state["due"] = (date.fromisoformat(career.date) + timedelta(days=delay)).isoformat()
    state["offer"] = clean
    state["counter"] = None
    state["agreed"] = None
    state["status"] = "pending"
    state["message"] = PENDING_MESSAGE
    if context["offer"] is not None:
        context["offer"]["contract_status"] = "pending"
    return state


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


def _resolve_one(career: Career, player_id: str, state: dict) -> None:
    player_value = max(int(state.get("value") or 0), MIN_MARKET_VALUE)
    offer = _clean_terms(state.get("offer") or {})
    demand = state.get("demand") or {}
    shortfalls = _term_shortfalls(offer, demand, player_value)
    if not shortfalls:
        state["status"] = "accepted"
        state["counter"] = None
        state["agreed"] = dict(offer)
        state["message"] = ACCEPTED_MESSAGE
    elif int(state.get("counter_offers") or 0) >= MAX_COUNTER_OFFERS:
        state["status"] = "refused"
        state["counter"] = None
        state["agreed"] = None
        state["message"] = REFUSED_MESSAGE
    else:
        state["counter_offers"] = int(state.get("counter_offers") or 0) + 1
        state["status"] = "counter"
        state["counter"] = _counter_terms(offer, demand, player_value, shortfalls)
        state["agreed"] = None
        state["message"] = " ".join(
            COUNTER_MESSAGES[key] for key in shortfalls if key in COUNTER_MESSAGES
        )


def resolve_transfer_contracts(career: Career) -> None:
    for player_id, state in career.transfer_contracts.items():
        if state.get("status") != "pending":
            continue
        due = state.get("due")
        if not due or career.date < str(due):
            continue
        try:
            _resolve_one(career, player_id, state)
        except ValueError:
            continue
        offer = find_offer(career, state.get("offer_id")) if state.get("offer_id") else None
        if offer is not None:
            offer["contract_status"] = state.get("status")


def accept_transfer_counter(career: Career, player_id: str) -> dict:
    state = career.transfer_contracts.get(str(player_id))
    if not state or state.get("status") != "counter" or not state.get("counter"):
        raise ValueError("there is no counter-offer to accept")
    terms = _clean_terms(state["counter"])
    state["status"] = "accepted"
    state["agreed"] = terms
    state["counter"] = None
    state["message"] = ACCEPTED_MESSAGE
    if state.get("offer_id"):
        offer = find_offer(career, state["offer_id"])
        if offer is not None:
            offer["contract_status"] = "accepted"
    return state


def _join_squad(career: Career, player_id: str, terms: dict, item: dict) -> None:
    if player_id not in career.player_ids:
        career.player_ids.append(player_id)
    contract = dict(terms)
    if item.get("kind") == "loan" and int(item.get("wage_share") or 100) < 100:
        share = max(0, min(100, int(item["wage_share"])))
        contract["weekly_wage"] = max(
            MIN_WEEKLY_WAGE,
            int(round(terms["weekly_wage"] * share / 100 / 100) * 100),
        )
    career.player_contracts[player_id] = contract
    career.player_values.setdefault(player_id, int(item.get("market_value") or MIN_MARKET_VALUE))
    career.player_ages.setdefault(player_id, int(item.get("age") or 25))
    career.player_transfers.pop(player_id, None)
    career.negotiations.pop(player_id, None)


def _affordable(career: Career, fee: int) -> bool:
    if career.balance is None:
        return True
    return int(fee) <= int(career.balance)


def _remove_offer(career: Career, offer_id: str | None) -> None:
    if not offer_id:
        return
    career.transfer_offers = [
        offer
        for offer in career.transfer_offers
        if str(offer.get("id")) != str(offer_id)
    ]


def sign_transfer_contract(career: Career, player: dict) -> dict:
    player_id = str(player["id"])
    state = career.transfer_contracts.get(player_id)
    if not state or state.get("status") != "accepted":
        raise ValueError("the contract is not agreed yet")
    terms = _clean_terms(state.get("agreed") or state.get("offer") or {})
    fee = int(state.get("fee") or 0)
    if not _affordable(career, fee):
        raise ValueError("not enough money to complete this transfer")
    execute_on = _execution_date(career.date)
    item = {
        "player_id": player_id,
        "offer_id": state.get("offer_id"),
        "kind": str(state.get("kind") or "transfer"),
        "fee": fee,
        "loan_fee": int(state.get("loan_fee") or 0),
        "wage_share": int(state.get("wage_share") or 100),
        "terms": dict(terms),
        "market_value": _player_value(career, player),
        "age": _player_age(player),
        "agreed_at": career.date,
        "execute_on": execute_on,
    }
    if career.balance is not None:
        career.balance = int(career.balance) - fee
    if execute_on == str(career.date)[:10]:
        _join_squad(career, player_id, terms, item)
        item["executed_at"] = career.date
        _remove_offer(career, state.get("offer_id"))
    else:
        career.pending_transfers.append(item)
        offer = find_offer(career, state.get("offer_id")) if state.get("offer_id") else None
        if offer is not None:
            offer["signed"] = True
            offer["signed_at"] = career.date
            offer["execute_on"] = execute_on
            offer["contract_status"] = "signed"
    career.transfer_history.append(
        {
            "player_id": player_id,
            "overall": round(
                float(state.get("overall") or player.get("overall") or 0), 1
            ),
            "from_club_id": None
            if not player.get("club_id")
            else str(player["club_id"]),
            "to_club_id": str(career.club_id),
            "fee": fee,
            "kind": str(state.get("kind") or "transfer"),
            "offer_id": state.get("offer_id"),
            "date": str(career.date)[:10],
            "status": "completed"
            if execute_on == str(career.date)[:10]
            else "signed",
        }
    )
    career.transfer_contracts.pop(player_id, None)
    career.journal.append(
        {
            "seq": len(career.journal) + 1,
            "type": "transfer.signed",
            "payload": {
                "player_id": player_id,
                "offer_id": state.get("offer_id"),
                "fee": fee,
                "contract": dict(terms),
                "execute_on": execute_on,
            },
        }
    )
    return item


def execute_pending_transfers(career: Career) -> list[str]:
    if not career.pending_transfers:
        return []
    if not transfer_window_open(career.date):
        return []
    remaining = []
    executed = []
    for item in career.pending_transfers:
        if career.date >= str(item.get("execute_on") or ""):
            player_id = str(item.get("player_id") or "")
            _join_squad(career, player_id, dict(item.get("terms") or {}), item)
            item["executed_at"] = career.date
            executed.append(player_id)
            career.journal.append(
                {
                    "seq": len(career.journal) + 1,
                    "type": "transfer.completed",
                    "payload": {"player_id": player_id, "offer_id": item.get("offer_id")},
                }
            )
            _remove_offer(career, item.get("offer_id"))
        else:
            remaining.append(item)
    career.pending_transfers = remaining
    return executed


def transfer_contract_view(career: Career, player_id: str) -> dict | None:
    state = career.transfer_contracts.get(str(player_id))
    if not state:
        return None
    fee = int(state.get("fee") or 0)
    status = str(state.get("status") or "pending")
    terms = state.get("agreed") or state.get("offer") or {}
    affordable = _affordable(career, fee)
    return {
        "player_id": str(state.get("player_id") or player_id),
        "offer_id": state.get("offer_id"),
        "kind": str(state.get("kind") or "transfer"),
        "fee": fee,
        "loan_fee": int(state.get("loan_fee") or 0),
        "wage_share": int(state.get("wage_share") or 100),
        "status": status,
        "offer": state.get("offer"),
        "counter": state.get("counter"),
        "agreed": state.get("agreed"),
        "terms": dict(terms) if terms else None,
        "due": state.get("due"),
        "counter_offers": int(state.get("counter_offers") or 0),
        "message": str(state.get("message") or ""),
        "affordable": affordable,
        "balance_after": None
        if career.balance is None
        else int(career.balance) - fee,
        "can_sign": status == "accepted" and affordable,
    }
