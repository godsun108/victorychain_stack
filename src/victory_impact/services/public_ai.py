from __future__ import annotations

import re
from typing import Iterable
from urllib.parse import urlencode

from ..schemas import PublicAiAction, PublicAiChatResponse


def _contains_any(text: str, needles: Iterable[str]) -> bool:
    return any(needle in text for needle in needles)


TOPIC_KEYWORDS: dict[str, set[str]] = {
    "wallet": {"vusd", "transfer", "wallet", "receipt", "receipts", "tx", "transaction", "balance", "cashout", "send"},
    "social": {"chat", "social", "community", "call", "video", "inbox", "moderation", "room", "rooms"},
    "gaming": {"game", "gaming", "chess", "poker", "checkers", "arcade", "console"},
    "news": {"news", "update", "report", "impact", "ledger", "proof"},
    "calendar": {"calendar", "schedule", "event", "plan", "planning"},
    "donate": {"donate", "donation", "charity", "fund", "support"},
}

INTENT_REQUIRED_FIELDS: dict[str, tuple[str, ...]] = {
    "send_vusd": ("recipient", "amount"),
    "create_calendar_event": ("title", "date"),
}

FOLLOW_UP_HINTS = {
    "that",
    "this",
    "it",
    "those",
    "them",
    "more",
    "details",
    "next",
    "continue",
    "again",
    "same",
    "how",
    "what",
    "where",
    "when",
    "why",
    "make",
    "change",
    "update",
    "rename",
    "move",
    "reschedule",
}

DATE_TERMS = {
    "today",
    "tomorrow",
    "tonight",
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
    "next week",
    "next month",
}

STOP_RECIPIENTS = {"a", "an", "the", "my", "our", "friend", "wallet", "address", "someone", "send", "transfer", "pay", "to"}


def _extract_topic(text: str) -> str | None:
    for topic, keywords in TOPIC_KEYWORDS.items():
        if _contains_any(text, keywords):
            return topic
    return None


def _normalize_history(history: list[str] | None) -> list[str]:
    if not history:
        return []
    return [entry.strip() for entry in history if entry and entry.strip()]


def _strip_role_prefix(text: str) -> str:
    if ":" not in text:
        return text.strip()
    prefix, rest = text.split(":", 1)
    if prefix.strip().lower() in {"user", "assistant", "system"}:
        return rest.strip()
    return text.strip()


def _topic_from_history(history: list[str] | None) -> str | None:
    recent = list(reversed(_normalize_history(history)))
    for entry in recent:
        topic = _extract_topic(_strip_role_prefix(entry).lower())
        if topic:
            return topic
    return None


def _is_follow_up_message(text: str) -> bool:
    words = [part for part in text.split() if part]
    if len(words) <= 4:
        return True
    return _contains_any(text, FOLLOW_UP_HINTS)


def _extract_intent(text: str) -> str | None:
    lowered = text.lower()
    has_transfer_verb = _contains_any(lowered, {"send", "transfer", "pay"})
    has_wallet_terms = _contains_any(lowered, {"vusd", "wallet", "tx", "transaction"}) or " to " in lowered
    if has_transfer_verb and has_wallet_terms:
        return "send_vusd"

    has_calendar_verb = _contains_any(lowered, {"create", "add", "schedule", "book", "set"})
    has_calendar_terms = _contains_any(lowered, {"calendar", "event", "meeting", "reminder"})
    if has_calendar_verb and has_calendar_terms:
        return "create_calendar_event"

    return None


def _intent_from_history(history: list[str] | None) -> str | None:
    for entry in reversed(_normalize_history(history)):
        intent = _extract_intent(_strip_role_prefix(entry))
        if intent:
            return intent
    return None


def _extract_amount(text: str) -> tuple[str, str | None] | tuple[None, None]:
    lowered = text.lower()
    match = re.search(r"\b(\d+(?:\.\d{1,2})?)\s*(vusd|usd)?\b", text, flags=re.IGNORECASE)
    if not match:
        return None, None
    amount = match.group(1)
    currency = match.group(2).upper() if match.group(2) else ("VUSD" if "vusd" in lowered else None)
    return amount, currency


def _extract_recipient(text: str) -> str | None:
    patterns = [
        r"\bchange\s+recipient\s+to\s+([a-zA-Z][a-zA-Z0-9_.-]{1,31})\b",
        r"\brecipient\s+to\s+([a-zA-Z][a-zA-Z0-9_.-]{1,31})\b",
        r"\bsend\s+\d+(?:\.\d{1,2})?\s*(?:vusd|usd)?\s+to\s+([a-zA-Z][a-zA-Z0-9_.-]{1,31})\b",
        r"\bsend\s+\d+(?:\.\d{1,2})?\s*(?:vusd|usd)?\s+([a-zA-Z][a-zA-Z0-9_.-]{1,31})\b",
        r"\bto\s+([a-zA-Z][a-zA-Z0-9_.-]{1,31})\b",
        r"\brecipient\s+(?:is\s+)?([a-zA-Z][a-zA-Z0-9_.-]{1,31})\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if not match:
            continue
        candidate = match.group(1).strip().lower()
        if candidate in STOP_RECIPIENTS:
            continue
        return match.group(1).strip()
    return None


def _extract_date(text: str) -> str | None:
    lowered = text.lower()
    iso = re.search(r"\b\d{4}-\d{2}-\d{2}\b", text)
    if iso:
        return iso.group(0)

    for term in DATE_TERMS:
        if term in lowered:
            return term

    return None


def _extract_title(text: str) -> str | None:
    quoted = re.search(r'"([^"]{3,80})"', text)
    if quoted:
        return quoted.group(1).strip()

    renamed = re.search(r"\brename\s+(?:event\s+)?to\s+([a-z0-9][a-z0-9\-\s]{2,60})", text, flags=re.IGNORECASE)
    if renamed:
        return renamed.group(1).strip().rstrip(".,!?")

    title_is = re.search(r"\btitle\s+(?:is|to)\s+([a-z0-9][a-z0-9\-\s]{2,60})", text, flags=re.IGNORECASE)
    if title_is:
        return title_is.group(1).strip().rstrip(".,!?")

    named = re.search(r"\b(?:called|named|titled)\s+([a-z0-9][a-z0-9\-\s]{2,60})", text, flags=re.IGNORECASE)
    if named:
        return named.group(1).strip().rstrip(".,!?")

    schedule_for = re.search(
        r"\b(?:schedule|add|create|book|set)\s+(?:an?\s+)?(?:calendar\s+)?(?:event\s+)?(?:for\s+)?([a-z0-9][a-z0-9\-\s]{2,80})",
        text,
        flags=re.IGNORECASE,
    )
    if schedule_for:
        candidate = schedule_for.group(1).strip().rstrip(".,!?")
        for separator in [" on ", " at ", " tomorrow", " today", " next week", " next month"]:
            if separator in candidate:
                candidate = candidate.split(separator, 1)[0].strip()
        if candidate and candidate not in {"calendar", "event", "meeting", "reminder"}:
            return candidate

    return None


def _extract_intent_slots(intent: str, text: str) -> dict[str, str]:
    slots: dict[str, str] = {}

    if intent == "send_vusd":
        recipient = _extract_recipient(text)
        if recipient:
            slots["recipient"] = recipient
        amount, currency = _extract_amount(text)
        if amount:
            slots["amount"] = amount
        if currency:
            slots["currency"] = currency

    if intent == "create_calendar_event":
        title = _extract_title(text)
        if title:
            slots["title"] = title
        event_date = _extract_date(text)
        if event_date:
            slots["date"] = event_date

    return slots


def _slots_from_conversation(intent: str, history: list[str] | None, message: str) -> dict[str, str]:
    slots: dict[str, str] = {}
    for entry in _normalize_history(history):
        slots.update(_extract_intent_slots(intent, _strip_role_prefix(entry)))
    slots.update(_extract_intent_slots(intent, message))
    return slots


def _missing_fields(intent: str, slots: dict[str, str]) -> list[str]:
    required = INTENT_REQUIRED_FIELDS.get(intent, ())
    return [field for field in required if not slots.get(field)]


def _build_execution_path(path: str, params: dict[str, str]) -> str:
    filtered = {key: value for key, value in params.items() if value}
    if not filtered:
        return path
    return f"{path}?{urlencode(filtered)}"


def _build_intent_response(intent: str, slots: dict[str, str], missing: list[str], from_context: bool = False) -> PublicAiChatResponse:
    prefix = "Continuing that thread: " if from_context else ""

    if intent == "send_vusd":
        actions = [
            PublicAiAction(label="Send vUSD", path="/wallet/send", description="Open transfer flow"),
            PublicAiAction(label="Wallet Receipts", path="/wallet", description="View donation and wallet records"),
            PublicAiAction(label="Launch Portal", path="/launch", description="Authenticate wallet session"),
        ]
        if missing:
            if len(missing) == 2:
                next_question = "Who should receive the transfer, and how much vUSD should I prepare?"
            elif "recipient" in missing:
                next_question = "Who should receive the transfer?"
            else:
                next_question = "How much vUSD should I prepare?"
            return PublicAiChatResponse(
                reply=f"{prefix}I can prepare a vUSD transfer, but I still need: {', '.join(missing)}.",
                suggested_actions=actions,
                intent=intent,
                slots=slots,
                missing_fields=missing,
                next_question=next_question,
            )

        currency = slots.get("currency", "VUSD")
        execution_path = _build_execution_path(
            "/wallet/send",
            {
                "recipient": slots.get("recipient", ""),
                "amount": slots.get("amount", ""),
                "currency": currency,
            },
        )
        return PublicAiChatResponse(
            reply=(
                f"{prefix}Ready to send {slots['amount']} {currency} to {slots['recipient']}. "
                "Open Send vUSD to confirm and submit."
            ),
            suggested_actions=actions,
            intent=intent,
            slots=slots,
            missing_fields=[],
            next_question=None,
            execution_ready=True,
            execution_type="navigate_wallet_send",
            execution_label="Confirm Transfer Draft",
            confirmation_prompt=f"Open Send vUSD with {slots['amount']} {currency} to {slots['recipient']}?",
            execution_path=execution_path,
            execution_payload={
                "recipient": slots.get("recipient", ""),
                "amount": slots.get("amount", ""),
                "currency": currency,
            },
        )

    if intent == "create_calendar_event":
        actions = [
            PublicAiAction(label="Calendar", path="/calendar", description="Open event planner"),
            PublicAiAction(label="AI Chat", path="/ai-chat", description="Continue planning with AI assistant"),
        ]
        if missing:
            if len(missing) == 2:
                next_question = "What is the event title, and when should it happen?"
            elif "title" in missing:
                next_question = "What should the event be called?"
            else:
                next_question = "When should the event happen?"
            return PublicAiChatResponse(
                reply=f"{prefix}I can prepare your calendar event, but I still need: {', '.join(missing)}.",
                suggested_actions=actions,
                intent=intent,
                slots=slots,
                missing_fields=missing,
                next_question=next_question,
            )

        normalized_date = slots.get("date", "")
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", normalized_date):
            normalized_date = f"{normalized_date}T09:00"
        return PublicAiChatResponse(
            reply=(
                f"{prefix}Ready to schedule '{slots['title']}' on {slots['date']}. "
                "Open Calendar to confirm and save it."
            ),
            suggested_actions=actions,
            intent=intent,
            slots=slots,
            missing_fields=[],
            next_question=None,
            execution_ready=True,
            execution_type="create_calendar_local",
            execution_label="Create Event Now",
            confirmation_prompt=f"Create calendar event '{slots['title']}' on {slots['date']} now?",
            execution_path=_build_execution_path(
                "/calendar",
                {
                    "title": slots.get("title", ""),
                    "date": normalized_date or slots.get("date", ""),
                },
            ),
            execution_payload={
                "title": slots.get("title", ""),
                "date": normalized_date or slots.get("date", ""),
            },
        )

    return PublicAiChatResponse(
        reply=f"{prefix}I can route you to the right service quickly.",
        suggested_actions=[PublicAiAction(label="Apps Hub", path="/", description="Browse all services")],
        intent=intent,
        slots=slots,
        missing_fields=missing,
        next_question=None,
    )


def _build_topic_response(topic: str, from_context: bool = False) -> PublicAiChatResponse:
    prefix = "Continuing that thread: " if from_context else ""
    if topic == "wallet":
        return PublicAiChatResponse(
            reply=(
                f"{prefix}For wallet transfers, use Send vUSD. Connect your wallet, enter your friend's address, "
                "submit transfer, then verify the transaction."
            ),
            suggested_actions=[
                PublicAiAction(label="Send vUSD", path="/wallet/send", description="Open transfer flow"),
                PublicAiAction(label="Wallet Receipts", path="/wallet", description="View donation and wallet records"),
                PublicAiAction(label="Launch Portal", path="/launch", description="Authenticate wallet session"),
            ],
        )
    if topic == "social":
        return PublicAiChatResponse(
            reply=f"{prefix}Use Social Services to launch chat rooms, calls, moderation tools, and shared notebook workflows.",
            suggested_actions=[
                PublicAiAction(label="Social Services", path="/social", description="Open social launcher"),
                PublicAiAction(label="Chat Room", path="/chat-room", description="Jump into room controls"),
            ],
        )
    if topic == "gaming":
        return PublicAiChatResponse(
            reply=f"{prefix}Use Gaming Services to launch preset game rooms or open the full game console in Chat Room.",
            suggested_actions=[
                PublicAiAction(label="Gaming Services", path="/gaming", description="Open gaming launcher"),
                PublicAiAction(label="Chat Room", path="/chat-room", description="Open custom game console"),
            ],
        )
    if topic == "news":
        return PublicAiChatResponse(
            reply=f"{prefix}News Services aggregates your latest impact updates and recent treasury disbursement activity.",
            suggested_actions=[
                PublicAiAction(label="News Services", path="/news", description="Open impact news feed"),
                PublicAiAction(label="Impact Reports", path="/reports", description="Open published reports"),
                PublicAiAction(label="Transparency Ledger", path="/ledger", description="View disbursement proofs"),
            ],
        )
    if topic == "calendar":
        return PublicAiChatResponse(
            reply=f"{prefix}Use Calendar to create and track launch events. Events are stored in-app for fast mobile access.",
            suggested_actions=[
                PublicAiAction(label="Calendar", path="/calendar", description="Open event planner"),
                PublicAiAction(label="AI Chat", path="/ai-chat", description="Continue planning with AI assistant"),
            ],
        )
    if topic == "donate":
        return PublicAiChatResponse(
            reply=f"{prefix}Use Donate to route support by category and issue compliant impact receipts.",
            suggested_actions=[
                PublicAiAction(label="Donate", path="/donate", description="Open donation flow"),
                PublicAiAction(label="Impact Dashboard", path="/impact", description="Track category performance"),
            ],
        )
    return PublicAiChatResponse(
        reply="I can route you to the right service quickly.",
        suggested_actions=[PublicAiAction(label="Apps Hub", path="/", description="Browse all services")],
    )


def build_public_ai_chat_response(message: str, history: list[str] | None = None) -> PublicAiChatResponse:
    clean = (message or "").strip()
    lowered = clean.lower()

    if not clean:
        return PublicAiChatResponse(
            reply=(
                "I can help with donations, vUSD transfers, wallet receipts, social rooms, gaming rooms, "
                "news, and calendar planning."
            ),
            suggested_actions=[
                PublicAiAction(label="Apps Hub", path="/", description="Open all services"),
                PublicAiAction(label="Send vUSD", path="/wallet/send", description="Transfer vUSD to a friend"),
                PublicAiAction(label="News", path="/news", description="View latest impact updates"),
                PublicAiAction(label="Calendar", path="/calendar", description="Plan launch activities"),
            ],
        )

    intent = _extract_intent(lowered)
    if intent:
        slots = _slots_from_conversation(intent, history, clean)
        missing = _missing_fields(intent, slots)
        return _build_intent_response(intent, slots, missing)

    history_intent = _intent_from_history(history)
    if history_intent and _is_follow_up_message(lowered):
        slots = _slots_from_conversation(history_intent, history, clean)
        missing = _missing_fields(history_intent, slots)
        return _build_intent_response(history_intent, slots, missing, from_context=True)

    topic = _extract_topic(lowered)
    if topic:
        return _build_topic_response(topic)

    history_topic = _topic_from_history(history)
    if history_topic and _is_follow_up_message(lowered):
        return _build_topic_response(history_topic, from_context=True)

    recent_context = ""
    recent = _normalize_history(history)
    if recent:
        recent_context = f" I kept context from {min(len(recent), 5)} recent messages."

    return PublicAiChatResponse(
        reply=(
            "I can route you to the right service quickly. Ask for wallet transfers, social, gaming, "
            f"news, calendar, or donations.{recent_context}"
        ),
        suggested_actions=[
            PublicAiAction(label="Apps Hub", path="/", description="Browse all services"),
            PublicAiAction(label="Social Services", path="/social", description="Open chat/call services"),
            PublicAiAction(label="Gaming Services", path="/gaming", description="Open game launchers"),
            PublicAiAction(label="News Services", path="/news", description="Open latest updates"),
            PublicAiAction(label="Calendar", path="/calendar", description="Open event planner"),
        ],
    )
