from __future__ import annotations

import hashlib
import random
from datetime import date, timedelta

from server.career.core import Career
from server.career.squad import MIN_SQUAD_SIZE
from server.career.transfer_contracts import (
    next_transfer_window,
    transfer_window_open,
)

OFFER_LIFETIME_DAYS = 30
DAILY_LIMIT = 2
RESPONSE_DAYS = (2, 3, 4)
FOREIGN_OVERALL_THRESHOLD = 75.0
MIN_MARKET_VALUE = 50_000
MAX_OVERALL_GAP = 9.0
MAX_FEE_SQUAD_SHARE = 0.30
MIN_OFFER_VALUE_SHARE = 0.75
TIER_LIMITS = ((82.0, 1), (75.0, 2), (68.0, 3), (60.0, 4))

ACTIVE_STATUSES = ("pending", "counter")

ROLE_TARGETS = {
    "GK": 2,
    "CB": 3,
    "LB": 1,
    "RB": 1,
    "DM": 1,
    "CM": 2,
    "LM": 1,
    "RM": 1,
    "AM": 1,
    "CF": 2,
}

PENDING_MESSAGE = "Клуб ждёт вашего ответа."
COUNTER_PENDING_MESSAGE = "Клуб обдумывает контрпредложение."
ACCEPTED_MESSAGE = "Предложение принято."
REFUSED_MESSAGE = "Вы отказались от предложения."
EXPIRED_MESSAGE = "Срок предложения истёк."
ACCEPTED_COUNTER_MESSAGE = "Клуб принял контрпредложение."
REFUSED_COUNTER_MESSAGE = "Клуб отклонил контрпредложение."


def _rng(career: Career, *parts: object) -> random.Random:
    return random.Random(":".join(str(part) for part in (career.seed, *parts)))


def _money(value: float) -> int:
    return max(0, int(round(value / 10_000) * 10_000))


def _player_value(career: Career, player: dict) -> int:
    player_id = str(player["id"])
    value = int(
        career.player_values.get(player_id)
        or player.get("market_value")
        or 0
    )
    return max(value, MIN_MARKET_VALUE)


def _player_overall(player: dict) -> float:
    return float(player.get("overall") or 0)


def _max_tier(overall: float) -> int:
    for threshold, tier in TIER_LIMITS:
        if overall >= threshold:
            return tier
    return 6


def _window_bounds(day: date) -> tuple[date, date] | None:
    if day.month == 1:
        return date(day.year, 1, 1), date(day.year, 1, 31)
    if day.month in (7, 8):
        return date(day.year, 7, 1), date(day.year, 8, 31)
    return None


def _pace(career: Career, day: date) -> tuple[int, int, bool]:
    bounds = _window_bounds(day)
    if bounds is not None:
        start, end = bounds
        bucket = max(0, (day - start).days // 7)
        rng = _rng(career, "incoming-pace", start.isoformat(), bucket)
        target = rng.choice((1, 2))
        deadline = day == end
        if deadline:
            target = 3 + rng.randrange(0, 3)
        return target, 6, deadline
    return 1, 13, False


def _created_between(career: Career, start: date, end: date) -> int:
    total = 0
    for offer in career.incoming_offers:
        created = str(offer.get("created_at") or "")
        if not created:
            continue
        try:
            day = date.fromisoformat(created[:10])
        except ValueError:
            continue
        if start <= day <= end:
            total += 1
    return total


def _created_on(career: Career, day: date) -> int:
    return sum(
        1
        for offer in career.incoming_offers
        if str(offer.get("created_at") or "")[:10] == day.isoformat()
    )


def _departing(career: Career, player_id: str) -> bool:
    return any(
        str(item.get("player_id")) == str(player_id)
        for item in career.pending_departures
    )


def _active_offer(
    career: Career, player_id: str, club_id: str
) -> dict | None:
    for offer in career.incoming_offers:
        if str(offer.get("player_id")) != str(player_id):
            continue
        if str(offer.get("club_id")) != str(club_id):
            continue
        if str(offer.get("status")) in ACTIVE_STATUSES:
            return offer
    return None


def _contract_months(career: Career, player: dict) -> int:
    player_id = str(player["id"])
    contract = career.player_contracts.get(player_id) or {}
    if contract.get("years"):
        return max(1, int(contract["years"]) * 12)
    if not player.get("club_id"):
        return 0
    rng = random.Random(f"{career.seed}:contract:{player_id}:months")
    return rng.randint(1, 60)


def _player_weight(career: Career, player: dict) -> float:
    player_id = str(player["id"])
    status = career.player_transfers.get(player_id)
    if status == "blocked":
        return 0.0
    weight = 1.0
    if status in ("transfer", "loan"):
        weight *= 5.0
    if _contract_months(career, player) <= 6:
        weight *= 3.0
    overall = _player_overall(player)
    weight *= 1.0 + max(0.0, overall - 65.0) / 12.0
    state = career.player_state.get(player_id) or {}
    stats = state.get("stats") or {}
    goals = int(stats.get("goals") or 0)
    assists = int(stats.get("assists") or 0)
    weight *= 1.0 + min(2.0, (goals + assists) / 12.0)
    return max(0.0, weight)


def _choose_player(
    career: Career, players: list[dict], rng: random.Random
) -> dict | None:
    pool = []
    weights = []
    for player in players:
        player_id = str(player["id"])
        if player_id not in career.player_ids:
            continue
        if _departing(career, player_id):
            continue
        weight = _player_weight(career, player)
        if weight <= 0:
            continue
        pool.append(player)
        weights.append(weight)
    if not pool:
        return None
    return rng.choices(pool, weights=weights, k=1)[0]


def _choose_kind(career: Career, player: dict, rng: random.Random) -> str:
    status = career.player_transfers.get(str(player["id"]))
    if status == "loan":
        return "loan"
    if status == "transfer":
        return "transfer"
    return "loan" if rng.random() < 0.15 else "transfer"


def _club_need(
    club_id: str, role: str, player: dict, roles: dict[str, dict[str, dict]]
) -> float:
    club_roles = roles.get(str(club_id)) or {}
    stats = club_roles.get(role) or {}
    count = int(stats.get("count") or 0)
    best = float(stats.get("best") or 0)
    target = ROLE_TARGETS.get(role, 1)
    need = float(max(0, target - count))
    if _player_overall(player) > best - 2.0:
        need += 1.0
    return need


def _buyer_candidates(
    career: Career,
    player: dict,
    clubs: list[dict],
    roles: dict[str, dict[str, dict]],
    club_stats: dict[str, dict] | None = None,
    kind: str = "transfer",
) -> tuple[list[dict], list[float]]:
    own_club_id = str(career.club_id)
    own_country = None
    for club in clubs:
        if str(club["id"]) == own_club_id:
            own_country = str(club.get("country_id") or "")
            break
    overall = _player_overall(player)
    foreign_allowed = overall >= FOREIGN_OVERALL_THRESHOLD
    max_tier = _max_tier(overall)
    value = _player_value(career, player)
    role = str(player.get("role") or "")
    candidates: list[dict] = []
    weights: list[float] = []
    for club in clubs:
        club_id = str(club["id"])
        if club_id == own_club_id:
            continue
        if not roles.get(club_id):
            continue
        foreign = str(club.get("country_id") or "") != own_country
        if foreign and not foreign_allowed:
            continue
        tier = int(club.get("tier_rank") or 99)
        if tier > max_tier:
            continue
        need = _club_need(club_id, role, player, roles)
        if need <= 0:
            continue
        stats = (club_stats or {}).get(club_id) or {}
        if stats:
            best = float(stats.get("best") or 0)
            if best and overall - best > MAX_OVERALL_GAP:
                continue
            squad_value = int(stats.get("value") or 0)
            if (
                kind == "transfer"
                and squad_value > 0
                and value * MIN_OFFER_VALUE_SHARE
                > squad_value * MAX_FEE_SQUAD_SHARE
            ):
                continue
        weight = need
        if not foreign:
            weight *= 1.6
        weight *= 1.0 if tier <= 1 else 0.8
        if stats:
            best = float(stats.get("best") or 0)
            if best:
                weight *= 1.0 + max(0.0, best - overall + 5.0) / 10.0
        candidates.append(club)
        weights.append(weight)
    return candidates, weights


def _offer_terms(
    career: Career, player: dict, kind: str, day: date, club_id: str
) -> dict:
    value = _player_value(career, player)
    rng = _rng(career, "incoming-terms", day.isoformat(), player["id"], club_id)
    if kind == "loan":
        fee = _money(value * rng.uniform(0.03, 0.08))
        demand_fee = max(fee, _money(value * rng.uniform(0.05, 0.12)))
        share = rng.choice((50, 60, 70, 80))
        demand_share = min(100, share + rng.choice((0, 10, 20)))
        return {
            "amount": fee,
            "loan_fee": fee,
            "wage_share": share,
            "demand": {
                "amount": demand_fee,
                "loan_fee": demand_fee,
                "wage_share": demand_share,
            },
        }
    fee = _money(value * rng.uniform(0.75, 1.1))
    demand = max(fee, _money(value * rng.uniform(1.0, 1.35)))
    return {
        "amount": fee,
        "loan_fee": 0,
        "wage_share": 0,
        "demand": {"amount": demand},
    }


def _offer_id(
    career: Career, player_id: str, club_id: str, day: date
) -> str:
    raw = (
        f"{career.seed}:incoming:{day.isoformat()}:{player_id}:{club_id}:"
        f"{len(career.incoming_offers)}:{len(career.journal)}"
    )
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def create_incoming_offer(
    career: Career,
    day: date,
    players: list[dict],
    clubs: list[dict],
    roles: dict[str, dict[str, dict]],
    club_stats: dict[str, dict] | None = None,
) -> dict | None:
    rng = _rng(career, "incoming-offer", day.isoformat(), len(career.incoming_offers))
    for _ in range(24):
        player = _choose_player(career, players, rng)
        if player is None:
            return None
        kind = _choose_kind(career, player, rng)
        candidates, weights = _buyer_candidates(
            career, player, clubs, roles, club_stats, kind
        )
        if not candidates:
            continue
        club = rng.choices(candidates, weights=weights, k=1)[0]
        player_id = str(player["id"])
        club_id = str(club["id"])
        if _active_offer(career, player_id, club_id) is not None:
            continue
        terms = _offer_terms(career, player, kind, day, club_id)
        offer = {
            "id": _offer_id(career, player_id, club_id, day),
            "player_id": player_id,
            "overall": round(float(player.get("overall") or 0), 1),
            "club_id": club_id,
            "club_name": str(club.get("name") or ""),
            "club_logo": str(club.get("logo") or ""),
            "club_country_id": str(club.get("country_id") or ""),
            "club_country_name": str(club.get("country_name") or ""),
            "club_league_name": str(club.get("league_name") or ""),
            "kind": kind,
            "amount": int(terms["amount"]),
            "loan_fee": int(terms["loan_fee"]),
            "wage_share": int(terms["wage_share"]),
            "status": "pending",
            "created_at": day.isoformat(),
            "expires_at": (
                day + timedelta(days=OFFER_LIFETIME_DAYS)
            ).isoformat(),
            "due": None,
            "responded_at": None,
            "counter_offers": 0,
            "counter": None,
            "acknowledged": False,
            "message": PENDING_MESSAGE,
            "demand": dict(terms["demand"]),
            "execute_on": None,
        }
        career.incoming_offers.append(offer)
        career.journal.append(
            {
                "seq": len(career.journal) + 1,
                "type": "transfer.received",
                "payload": {
                    "offer_id": offer["id"],
                    "player_id": player_id,
                    "club_id": club_id,
                    "kind": kind,
                    "amount": int(terms["amount"]),
                },
            }
        )
        return offer
    return None


def generate_incoming_offers(
    career: Career,
    previous_date: str,
    target_date: str,
    players: list[dict],
    clubs: list[dict],
    roles: dict[str, dict[str, dict]],
    club_stats: dict[str, dict] | None = None,
) -> None:
    try:
        current = date.fromisoformat(previous_date[:10])
        target = date.fromisoformat(target_date[:10])
    except ValueError:
        return
    if target < current:
        return
    day = current + timedelta(days=1)
    while day <= target:
        pace_target, lookback, deadline = _pace(career, day)
        created = _created_between(
            career, day - timedelta(days=lookback), day
        )
        daily = _created_on(career, day)
        while created < pace_target:
            if not deadline and daily >= DAILY_LIMIT:
                break
            offer = create_incoming_offer(
                career, day, players, clubs, roles, club_stats
            )
            if offer is None:
                break
            created += 1
            daily += 1
        day += timedelta(days=1)
    resolve_incoming_offers(career)


def find_incoming_offer(career: Career, offer_id: str) -> dict | None:
    offer_id = str(offer_id)
    for offer in career.incoming_offers:
        if str(offer.get("id")) == offer_id:
            return offer
    return None


def _remove_player(career: Career, player_id: str) -> None:
    player_id = str(player_id)
    if player_id in career.player_ids:
        career.player_ids.remove(player_id)
    if career.lineup:
        career.lineup = [item for item in career.lineup if item != player_id]
    if career.bench_order:
        career.bench_order = [
            item for item in career.bench_order if item != player_id
        ]
    career.player_state.pop(player_id, None)
    career.player_contracts.pop(player_id, None)
    career.player_values.pop(player_id, None)
    career.player_ages.pop(player_id, None)
    career.shirt_numbers.pop(player_id, None)
    career.player_transfers.pop(player_id, None)
    career.negotiations.pop(player_id, None)
    career.transfer_contracts.pop(player_id, None)
    if player_id in career.shortlist:
        career.shortlist.remove(player_id)


def _execute_departure(career: Career, item: dict) -> None:
    player_id = str(item.get("player_id") or "")
    if player_id not in career.player_ids:
        return
    _remove_player(career, player_id)
    fee = int(item.get("fee") or 0)
    if career.balance is not None:
        career.balance = int(career.balance) + fee
    item["executed_at"] = career.date
    offer = find_incoming_offer(career, item.get("offer_id") or "")
    if offer is not None:
        offer["executed_at"] = career.date
    career.journal.append(
        {
            "seq": len(career.journal) + 1,
            "type": "transfer.departure",
            "payload": {
                "player_id": player_id,
                "club_id": item.get("club_id"),
                "offer_id": item.get("offer_id"),
                "fee": fee,
            },
        }
    )


def _complete_accept(career: Career, offer: dict) -> None:
    when = career.date
    offer["status"] = "accepted"
    offer["counter"] = None
    offer["responded_at"] = when
    execute_on = (
        when if transfer_window_open(when) else next_transfer_window(when)
    )
    offer["execute_on"] = execute_on
    career.transfer_history.append(
        {
            "player_id": str(offer["player_id"]),
            "overall": round(float(offer.get("overall") or 0), 1),
            "from_club_id": str(career.club_id),
            "to_club_id": str(offer.get("club_id") or ""),
            "fee": int(offer.get("amount") or 0),
            "kind": str(offer.get("kind") or "transfer"),
            "offer_id": str(offer["id"]),
            "date": str(when)[:10],
            "status": "completed"
            if execute_on == str(when)[:10]
            else "agreed",
        }
    )
    if execute_on == str(when)[:10]:
        offer["message"] = ACCEPTED_MESSAGE
        _execute_departure(
            career,
            {
                "player_id": str(offer["player_id"]),
                "club_id": str(offer.get("club_id") or ""),
                "offer_id": str(offer["id"]),
                "fee": int(offer.get("amount") or 0),
            },
        )
        offer["executed_at"] = when
        return
    offer["message"] = (
        f"Переход согласован и состоится {execute_on}."
    )
    career.pending_departures.append(
        {
            "player_id": str(offer["player_id"]),
            "club_id": str(offer.get("club_id") or ""),
            "offer_id": str(offer["id"]),
            "kind": str(offer.get("kind") or "transfer"),
            "fee": int(offer.get("amount") or 0),
            "execute_on": execute_on,
            "agreed_at": when,
        }
    )


def accept_incoming_offer(career: Career, offer_id: str) -> dict:
    offer = find_incoming_offer(career, offer_id)
    if offer is None:
        raise ValueError("offer not found")
    if str(offer.get("status")) != "pending":
        raise ValueError("this offer cannot be accepted")
    player_id = str(offer.get("player_id"))
    if player_id not in career.player_ids:
        raise ValueError("player is not in this squad")
    if len(career.player_ids) <= MIN_SQUAD_SIZE:
        raise ValueError("the squad cannot drop below 11 players")
    offer["acknowledged"] = True
    _complete_accept(career, offer)
    career.journal.append(
        {
            "seq": len(career.journal) + 1,
            "type": "transfer.incoming.accepted",
            "payload": {
                "offer_id": str(offer["id"]),
                "player_id": player_id,
                "club_id": str(offer.get("club_id") or ""),
                "fee": int(offer.get("amount") or 0),
                "execute_on": offer.get("execute_on"),
            },
        }
    )
    return offer


def refuse_incoming_offer(career: Career, offer_id: str) -> dict:
    offer = find_incoming_offer(career, offer_id)
    if offer is None:
        raise ValueError("offer not found")
    if str(offer.get("status")) != "pending":
        raise ValueError("this offer cannot be refused")
    offer["status"] = "refused"
    offer["acknowledged"] = True
    offer["responded_at"] = career.date
    offer["message"] = REFUSED_MESSAGE
    career.journal.append(
        {
            "seq": len(career.journal) + 1,
            "type": "transfer.incoming.refused",
            "payload": {
                "offer_id": str(offer["id"]),
                "player_id": str(offer.get("player_id")),
            },
        }
    )
    return offer


def _counter_due(career: Career, offer: dict) -> str:
    rng = _rng(career, "incoming-response", offer["id"])
    delay = rng.choice(RESPONSE_DAYS)
    return (date.fromisoformat(career.date) + timedelta(days=delay)).isoformat()


def counter_incoming_offer(
    career: Career, offer_id: str, amount: int
) -> dict:
    offer = find_incoming_offer(career, offer_id)
    if offer is None:
        raise ValueError("offer not found")
    if str(offer.get("status")) != "pending":
        raise ValueError("this offer cannot be countered")
    if int(offer.get("counter_offers") or 0) >= 1:
        raise ValueError("only one counter-offer is allowed")
    value = int(amount or 0)
    if value <= 0:
        raise ValueError("counter-offer amount must be positive")
    if value <= int(offer.get("amount") or 0):
        raise ValueError("counter-offer must be higher than the current offer")
    offer["status"] = "counter"
    offer["counter_offers"] = 1
    offer["counter"] = {
        "amount": value,
        "loan_fee": value if offer.get("kind") == "loan" else 0,
        "wage_share": int(offer.get("wage_share") or 0),
    }
    offer["due"] = _counter_due(career, offer)
    offer["acknowledged"] = True
    offer["message"] = COUNTER_PENDING_MESSAGE
    career.journal.append(
        {
            "seq": len(career.journal) + 1,
            "type": "transfer.incoming.countered",
            "payload": {
                "offer_id": str(offer["id"]),
                "player_id": str(offer.get("player_id")),
                "amount": value,
            },
        }
    )
    return offer


def _expire(career: Career, offer: dict) -> None:
    offer["status"] = "expired"
    offer["acknowledged"] = False
    offer["responded_at"] = career.date
    offer["message"] = EXPIRED_MESSAGE


def resolve_incoming_offers(career: Career) -> None:
    for offer in career.incoming_offers:
        status = str(offer.get("status"))
        if status not in ACTIVE_STATUSES:
            continue
        expires_at = offer.get("expires_at")
        if expires_at and career.date >= str(expires_at):
            _expire(career, offer)
            continue
        if status != "counter":
            continue
        due = offer.get("due")
        if not due or career.date < str(due):
            continue
        counter = offer.get("counter") or {}
        demand = offer.get("demand") or {}
        amount = int(counter.get("amount") or 0)
        willing = int(demand.get("amount") or 0)
        offer["acknowledged"] = False
        offer["responded_at"] = career.date
        if amount <= willing and len(career.player_ids) > MIN_SQUAD_SIZE:
            offer["message"] = ACCEPTED_COUNTER_MESSAGE
            _complete_accept(career, offer)
        else:
            offer["status"] = "refused"
            offer["counter"] = None
            offer["message"] = REFUSED_COUNTER_MESSAGE
        career.journal.append(
            {
                "seq": len(career.journal) + 1,
                "type": "transfer.incoming.response",
                "payload": {
                    "offer_id": str(offer["id"]),
                    "player_id": str(offer.get("player_id")),
                    "status": str(offer.get("status")),
                },
            }
        )


def execute_pending_departures(career: Career) -> list[str]:
    if not career.pending_departures:
        return []
    if not transfer_window_open(career.date):
        return []
    remaining = []
    executed = []
    for item in career.pending_departures:
        if career.date >= str(item.get("execute_on") or ""):
            player_id = str(item.get("player_id") or "")
            _execute_departure(career, item)
            executed.append(player_id)
        else:
            remaining.append(item)
    career.pending_departures = remaining
    return executed


def acknowledge_incoming_offer(career: Career, offer_id: str) -> dict:
    offer = find_incoming_offer(career, offer_id)
    if offer is None:
        raise ValueError("offer not found")
    offer["acknowledged"] = True
    return offer


def incoming_offer_view(career: Career, offer: dict) -> dict:
    status = str(offer.get("status"))
    counter = offer.get("counter")
    counter_view = (
        {key: int(value) for key, value in counter.items()}
        if isinstance(counter, dict)
        else None
    )
    can_accept = (
        status == "pending"
        and str(offer.get("player_id")) in career.player_ids
        and len(career.player_ids) > MIN_SQUAD_SIZE
    )
    return {
        "offer_id": str(offer.get("id") or ""),
        "kind": str(offer.get("kind") or "transfer"),
        "amount": int(offer.get("amount") or 0),
        "loan_fee": int(offer.get("loan_fee") or 0),
        "wage_share": int(offer.get("wage_share") or 0),
        "status": status,
        "created_at": offer.get("created_at"),
        "expires_at": offer.get("expires_at"),
        "due": offer.get("due"),
        "responded_at": offer.get("responded_at"),
        "counter_offers": int(offer.get("counter_offers") or 0),
        "counter": counter_view,
        "message": str(offer.get("message") or ""),
        "acknowledged": bool(offer.get("acknowledged")),
        "club_id": str(offer.get("club_id") or ""),
        "club_name": str(offer.get("club_name") or ""),
        "club_logo": str(offer.get("club_logo") or ""),
        "club_country_id": str(offer.get("club_country_id") or ""),
        "club_country_name": str(offer.get("club_country_name") or ""),
        "club_league_name": str(offer.get("club_league_name") or ""),
        "execute_on": offer.get("execute_on"),
        "executed_at": offer.get("executed_at"),
        "can_accept": can_accept,
        "can_refuse": status == "pending",
        "can_counter": status == "pending"
        and int(offer.get("counter_offers") or 0) < 1,
        "unread": not bool(offer.get("acknowledged")),
    }
