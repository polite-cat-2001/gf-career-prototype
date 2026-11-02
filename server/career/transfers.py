from __future__ import annotations

import hashlib
import random
from datetime import date, timedelta

from server.career.core import Career

OFFER_KINDS = ("transfer", "loan")
ACTIVE_OFFER_STATUSES = ("pending", "counter")
MAX_COUNTER_OFFERS = 2
RESPONSE_DAYS = (2, 3, 4)
RETRY_DAYS = 7
MIN_MARKET_VALUE = 50_000

PENDING_MESSAGE = "Клуб обдумывает предложение."
ACCEPTED_MESSAGE = "Клуб принял предложение."
REFUSED_MESSAGE = "Клуб отклонил предложение."
COUNTER_MESSAGE = "Клуб предлагает новые условия."


def _offer_rng(career: Career, offer_id: str, salt: str) -> random.Random:
    return random.Random(f"{career.seed}:offer:{offer_id}:{salt}")


def _player_value(player: dict) -> int:
    return max(int(player.get("market_value") or 0), MIN_MARKET_VALUE)


def _offer_id(career: Career, player_id: str, kind: str) -> str:
    raw = (
        f"{career.seed}:{career.date}:{player_id}:{kind}:"
        f"{len(career.transfer_offers)}:{len(career.journal)}"
    )
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def _offer_demand(career: Career, offer_id: str, player: dict, kind: str) -> dict:
    value = _player_value(player)
    if kind == "transfer":
        rng = _offer_rng(career, offer_id, "transfer-demand")
        return {"value": value, "fee": int(value * rng.uniform(0.85, 1.05))}
    rng = _offer_rng(career, offer_id, "loan-demand")
    return {
        "value": value,
        "fee": max(1_000, int(value * rng.uniform(0.04, 0.08))),
        "wage_share": rng.choice((50, 60, 70, 80)),
    }


def _response_due(career: Career, offer: dict) -> str:
    rounds = int(offer.get("counter_offers") or 0)
    rng = _offer_rng(career, str(offer["id"]), f"delay:{rounds}")
    delay = rng.choice(RESPONSE_DAYS)
    return (date.fromisoformat(career.date) + timedelta(days=delay)).isoformat()


def find_offer(career: Career, offer_id: str) -> dict | None:
    offer_id = str(offer_id)
    for offer in career.transfer_offers:
        if str(offer.get("id")) == offer_id:
            return offer
    return None


def _active_offer(career: Career, player_id: str) -> dict | None:
    for offer in career.transfer_offers:
        if str(offer.get("player_id")) != str(player_id):
            continue
        if str(offer.get("status")) in ACTIVE_OFFER_STATUSES:
            return offer
    return None


def _retry_offer(career: Career, player_id: str) -> dict | None:
    latest = None
    for offer in career.transfer_offers:
        if str(offer.get("player_id")) != str(player_id):
            continue
        if str(offer.get("status")) != "refused":
            continue
        retry_after = offer.get("retry_after")
        if not retry_after:
            continue
        if latest is None or str(retry_after) > str(latest.get("retry_after")):
            latest = offer
    return latest


def _journal(career: Career, kind: str, payload: dict) -> None:
    career.journal.append(
        {
            "seq": len(career.journal) + 1,
            "type": kind,
            "payload": payload,
        }
    )


def _clean_transfer(
    career: Career,
    player: dict,
    *,
    amount: int | None,
    buyout: bool,
) -> tuple[int, bool]:
    player_id = str(player["id"])
    if player_id in career.player_ids:
        raise ValueError("you cannot make an offer for your own player")
    amount = int(amount or 0)
    if amount < 0:
        raise ValueError("offer amount cannot be negative")
    release_clause = int(player.get("release_clause") or 0)
    if buyout:
        if not player.get("club_id") or release_clause <= 0:
            raise ValueError("release clause is not available for this player")
        amount = release_clause
    if career.balance is not None and amount > int(career.balance):
        raise ValueError("offer amount is above the club balance")
    return amount, bool(buyout)


def _clean_loan(
    career: Career,
    player: dict,
    *,
    amount: int | None,
    loan_fee: int | None,
    wage_share: int | None,
) -> tuple[int, int]:
    player_id = str(player["id"])
    if player_id in career.player_ids:
        raise ValueError("you cannot make an offer for your own player")
    fee = int(loan_fee if loan_fee is not None else amount or 0)
    if fee < 0:
        raise ValueError("loan fee cannot be negative")
    if career.balance is not None and fee > int(career.balance):
        raise ValueError("loan fee is above the club balance")
    share = int(wage_share or 0)
    if not 0 <= share <= 100:
        raise ValueError("wage share must be between 0 and 100")
    return fee, share


def _update_offer_terms(
    offer: dict,
    *,
    kind: str,
    amount: int,
    loan_fee: int,
    wage_share: int,
    buyout: bool,
) -> None:
    offer["kind"] = kind
    offer["amount"] = int(amount)
    offer["loan_fee"] = int(loan_fee)
    offer["wage_share"] = int(wage_share)
    offer["buyout"] = bool(buyout)


def create_transfer_offer(
    career: Career,
    player: dict,
    *,
    kind: str = "transfer",
    amount: int | None = None,
    loan_fee: int | None = None,
    wage_share: int | None = None,
    buyout: bool = False,
) -> dict:
    player_id = str(player["id"])
    kind = str(kind or "transfer")
    if kind not in OFFER_KINDS:
        raise ValueError("unknown offer kind")
    existing = [
        offer
        for offer in career.transfer_offers
        if str(offer.get("player_id")) == player_id
    ]
    active = _active_offer(career, player_id)
    if active is not None and str(active.get("status")) == "pending":
        raise ValueError("there is already an active offer for this player")
    if active is not None and str(active.get("kind")) != kind:
        raise ValueError("there is already an active offer for this player")
    retry = _retry_offer(career, player_id)
    if retry is not None and str(retry.get("retry_after") or "") > career.date:
        raise ValueError(f"you can make another offer after {retry['retry_after']}")
    if active is None and existing:
        latest = existing[-1]
        if str(latest.get("status")) == "accepted":
            raise ValueError(
                "the club has already accepted an offer for this player"
            )

    if kind == "transfer":
        amount, buyout = _clean_transfer(career, player, amount=amount, buyout=buyout)
        loan_fee, wage_share = 0, 0
    else:
        if buyout:
            raise ValueError("buyout is only available for a transfer")
        loan_fee, wage_share = _clean_loan(
            career,
            player,
            amount=amount,
            loan_fee=loan_fee,
            wage_share=wage_share,
        )
        amount, buyout = loan_fee, False

    if active is not None:
        offer = active
        career.transfer_offers = [
            item for item in career.transfer_offers if item is not offer
        ]
        _update_offer_terms(
            offer,
            kind=kind,
            amount=amount,
            loan_fee=loan_fee,
            wage_share=wage_share,
            buyout=buyout,
        )
        offer["status"] = "pending"
        offer["counter"] = None
        offer["responded_at"] = None
        offer["due"] = _response_due(career, offer)
        offer["message"] = PENDING_MESSAGE
        career.transfer_offers.append(offer)
        _journal(
            career,
            "transfer.offer.sent",
            {
                "offer_id": str(offer["id"]),
                "player_id": player_id,
                "kind": kind,
                "amount": amount,
            },
        )
        return offer

    career.transfer_offers = [
        offer
        for offer in career.transfer_offers
        if str(offer.get("player_id")) != player_id
    ]
    offer_id = _offer_id(career, player_id, kind)
    offer = {
        "id": offer_id,
        "player_id": player_id,
        "kind": kind,
        "amount": int(amount),
        "loan_fee": int(loan_fee),
        "wage_share": int(wage_share),
        "buyout": bool(buyout),
        "status": "pending",
        "due": None,
        "created_at": career.date,
        "responded_at": None,
        "counter_offers": 0,
        "counter": None,
        "retry_after": None,
        "message": PENDING_MESSAGE,
        "demand": _offer_demand(career, offer_id, player, kind),
    }
    offer["due"] = _response_due(career, offer)
    career.transfer_offers.append(offer)
    _journal(
        career,
        "transfer.offer.sent",
        {
            "offer_id": offer_id,
            "player_id": player_id,
            "kind": kind,
            "amount": int(amount),
        },
    )
    return offer


def _accept(offer: dict, when: str) -> None:
    offer["status"] = "accepted"
    offer["counter"] = None
    offer["message"] = ACCEPTED_MESSAGE
    offer["responded_at"] = when


def _refuse(offer: dict, when: str) -> None:
    offer["status"] = "refused"
    offer["counter"] = None
    offer["message"] = REFUSED_MESSAGE
    offer["responded_at"] = when
    offer["retry_after"] = (
        date.fromisoformat(when) + timedelta(days=RETRY_DAYS)
    ).isoformat()


def _counter(career: Career, offer: dict, terms: dict, when: str) -> None:
    offer["counter_offers"] = int(offer.get("counter_offers") or 0) + 1
    offer["status"] = "counter"
    offer["counter"] = {key: int(value) for key, value in terms.items()}
    offer["message"] = COUNTER_MESSAGE
    offer["responded_at"] = when


def _resolve_one(career: Career, offer: dict) -> None:
    when = career.date
    if offer.get("buyout"):
        _accept(offer, when)
        return
    demand = offer.get("demand") or {}
    rounds = int(offer.get("counter_offers") or 0)
    if str(offer.get("kind")) == "loan":
        fee = int(offer.get("loan_fee") or 0)
        share = int(offer.get("wage_share") or 0)
        fee_demand = int(demand.get("fee") or 0)
        share_demand = int(demand.get("wage_share") or 0)
        if fee >= fee_demand and share >= share_demand:
            _accept(offer, when)
        elif rounds >= MAX_COUNTER_OFFERS:
            _refuse(offer, when)
        elif fee * 100 >= fee_demand * 50 or share + 20 >= share_demand:
            counter_fee = max(fee, fee_demand)
            _counter(
                career,
                offer,
                {
                    "amount": counter_fee,
                    "loan_fee": counter_fee,
                    "wage_share": max(share, share_demand),
                },
                when,
            )
        else:
            _refuse(offer, when)
        return

    fee = int(offer.get("amount") or 0)
    fee_demand = int(demand.get("fee") or 0)
    if fee >= fee_demand:
        _accept(offer, when)
    elif rounds >= MAX_COUNTER_OFFERS:
        _refuse(offer, when)
    elif fee * 100 >= fee_demand * 65:
        _counter(career, offer, {"amount": fee_demand}, when)
    else:
        _refuse(offer, when)


def resolve_transfer_offers(career: Career) -> None:
    for offer in career.transfer_offers:
        if str(offer.get("status")) != "pending":
            continue
        due = offer.get("due")
        if not due or career.date < str(due):
            continue
        _resolve_one(career, offer)


def _counter_affordable(career: Career, offer: dict) -> bool:
    counter = offer.get("counter") or {}
    fee = int(counter.get("amount") or 0)
    if career.balance is None:
        return True
    return fee <= int(career.balance)


def accept_offer_counter(career: Career, offer_id: str) -> dict:
    offer = find_offer(career, offer_id)
    if offer is None:
        raise ValueError("offer not found")
    if str(offer.get("status")) != "counter" or not offer.get("counter"):
        raise ValueError("there is no counter-offer to accept")
    if not _counter_affordable(career, offer):
        raise ValueError("not enough money to accept these terms")
    counter = offer["counter"]
    offer["amount"] = int(counter.get("amount") or 0)
    if str(offer.get("kind")) == "loan":
        offer["loan_fee"] = int(counter.get("loan_fee") or counter.get("amount") or 0)
        offer["wage_share"] = int(counter.get("wage_share") or 0)
    offer["status"] = "accepted"
    offer["counter"] = None
    offer["message"] = ACCEPTED_MESSAGE
    offer["responded_at"] = career.date
    _journal(
        career,
        "transfer.offer.accepted",
        {"offer_id": str(offer["id"]), "player_id": str(offer["player_id"])},
    )
    return offer


def offer_view(career: Career, offer: dict) -> dict:
    status = str(offer.get("status"))
    counter = offer.get("counter")
    counter_view = (
        {key: int(value) for key, value in counter.items()}
        if isinstance(counter, dict)
        else None
    )
    affordable = _counter_affordable(career, offer) if counter_view else True
    retry_after = offer.get("retry_after")
    if status == "counter":
        can_offer_again = True
    elif status == "refused":
        can_offer_again = not retry_after or career.date >= str(retry_after)
    elif status == "withdrawn":
        can_offer_again = True
    else:
        can_offer_again = False
    return {
        "offer_id": str(offer.get("id") or ""),
        "kind": str(offer.get("kind") or "transfer"),
        "amount": int(offer.get("amount") or 0),
        "loan_fee": int(offer.get("loan_fee") or 0),
        "wage_share": int(offer.get("wage_share") or 0),
        "buyout": bool(offer.get("buyout")),
        "status": status,
        "due": offer.get("due"),
        "created_at": offer.get("created_at"),
        "responded_at": offer.get("responded_at"),
        "counter_offers": int(offer.get("counter_offers") or 0),
        "counter": counter_view,
        "retry_after": retry_after,
        "message": str(offer.get("message") or ""),
        "can_offer_again": can_offer_again,
        "can_accept_counter": status == "counter"
        and counter_view is not None
        and affordable,
        "affordable": affordable,
        "signed": bool(offer.get("signed")),
        "signed_at": offer.get("signed_at"),
        "execute_on": offer.get("execute_on"),
        "contract_status": offer.get("contract_status"),
        "can_negotiate": status == "accepted" and not bool(offer.get("signed")),
    }
