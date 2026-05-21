from src.victory_impact.services.public_ai import build_public_ai_chat_response


def _paths(response) -> set[str]:
    return {action.path for action in response.suggested_actions}


def test_public_ai_chat_follow_up_uses_recent_topic_context():
    history = [
        "user: I want to manage social chat rooms",
        "assistant: Use Social Services to launch chat rooms.",
    ]

    response = build_public_ai_chat_response("what next?", history)

    assert response.reply.startswith("Continuing that thread:")
    assert "/social" in _paths(response)
    assert "/chat-room" in _paths(response)


def test_public_ai_chat_direct_topic_overrides_history_context():
    history = [
        "user: show social controls",
        "assistant: Use Social Services.",
    ]

    response = build_public_ai_chat_response("show wallet receipts", history)

    assert "wallet" in response.reply.lower()
    assert "/wallet/send" in _paths(response)
    assert "/wallet" in _paths(response)


def test_public_ai_chat_direct_topic_routing_still_works():
    response = build_public_ai_chat_response("help me plan my calendar events", history=None)

    assert "calendar" in response.reply.lower()
    assert "/calendar" in _paths(response)


def test_public_ai_chat_send_vusd_slot_filling_requests_missing_fields():
    response = build_public_ai_chat_response("send vusd", history=None)

    assert response.intent == "send_vusd"
    assert set(response.missing_fields) == {"recipient", "amount"}
    assert response.next_question is not None
    assert "/wallet/send" in _paths(response)


def test_public_ai_chat_follow_up_updates_send_vusd_amount():
    history = [
        "user: send 25 vusd to alex",
        "assistant: Ready to send 25 VUSD to Alex.",
    ]

    response = build_public_ai_chat_response("make it 75", history)

    assert response.intent == "send_vusd"
    assert response.slots.get("recipient", "").lower() == "alex"
    assert response.slots.get("amount") == "75"
    assert response.missing_fields == []
    assert response.execution_ready is True
    assert response.execution_type == "navigate_wallet_send"
    assert response.execution_path is not None and response.execution_path.startswith("/wallet/send")


def test_public_ai_chat_calendar_intent_requests_missing_date():
    response = build_public_ai_chat_response('create calendar event called "Sprint Review"', history=None)

    assert response.intent == "create_calendar_event"
    assert response.slots.get("title") == "Sprint Review"
    assert response.missing_fields == ["date"]
    assert response.next_question is not None


def test_public_ai_chat_follow_up_can_change_recipient():
    history = [
        "user: send 40 vusd to alex",
        "assistant: Ready to send 40 VUSD to Alex.",
    ]
    response = build_public_ai_chat_response("change recipient to jordan", history)

    assert response.intent == "send_vusd"
    assert response.slots.get("recipient", "").lower() == "jordan"
    assert response.slots.get("amount") == "40"
    assert response.missing_fields == []


def test_public_ai_chat_follow_up_can_rename_event():
    history = [
        'user: create calendar event called "Sprint Review" tomorrow',
        "assistant: Ready to schedule it.",
    ]
    response = build_public_ai_chat_response('rename event to "Team Sync"', history)

    assert response.intent == "create_calendar_event"
    assert response.slots.get("title") == "Team Sync"
    assert response.slots.get("date") == "tomorrow"
    assert response.execution_ready is True
    assert response.execution_type == "create_calendar_local"
