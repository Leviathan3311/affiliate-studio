from datetime import UTC, datetime, timedelta

from app.social.policy import ActiveHours, PolicyInput, evaluate

HOURS = ActiveHours("Asia/Ho_Chi_Minh", "08:00", "22:00")
# 10:00 and 23:30 Vietnam time
DAY = datetime(2026, 10, 31, 3, 0, tzinfo=UTC)
NIGHT = datetime(2026, 10, 31, 16, 30, tzinfo=UTC)


def p(now, **kw):
    base = {
        "now": now,
        "hours": HOURS,
        "purpose": "response",
        "actor": "ai",
        "last_customer_message_at": now - timedelta(minutes=5),
    }
    return evaluate(PolicyInput(**(base | kw)))


def test_active_window_and_next_start():
    assert HOURS.is_active(DAY)
    assert not HOURS.is_active(NIGHT)
    # 23:30 -> next 08:00 local = 01:00 UTC next day
    assert HOURS.next_start(NIGHT) == datetime(2026, 11, 1, 1, 0, tzinfo=UTC)
    early = datetime(2026, 10, 31, 0, 0, tzinfo=UTC)  # 07:00 local -> same-day 08:00
    assert HOURS.next_start(early) == datetime(2026, 10, 31, 1, 0, tzinfo=UTC)


def test_allow_inside_window_during_day():
    assert p(DAY).decision == "ALLOW"


def test_ai_held_at_night_but_human_allowed():
    r = p(NIGHT)
    assert (r.decision, r.reasons) == ("HOLD", ["quiet_hours"])
    assert r.hold_until == HOURS.next_start(NIGHT)
    assert p(NIGHT, actor="human").decision == "ALLOW"
    assert p(NIGHT, actor="system", purpose="quiet_ack").decision == "ALLOW"


def test_outside_24h_window_is_skipped_even_for_humans():
    old = DAY - timedelta(hours=25)
    assert p(DAY, actor="human", last_customer_message_at=old).reasons == ["outside_24h_window"]
    assert p(DAY, last_customer_message_at=None).decision == "SKIP"


def test_opt_out_and_pause_take_precedence():
    assert p(DAY, actor="human", opted_out=True).reasons == ["customer_opted_out"]
    assert p(DAY, automation_paused=True).reasons == ["automation_paused"]
    assert p(DAY, actor="human", automation_paused=True).decision == "ALLOW"


def test_marketing_requires_opt_in():
    assert p(DAY, purpose="marketing").reasons == ["marketing_opt_in_required"]
    assert p(DAY, purpose="marketing", marketing_opt_in=True).decision == "ALLOW"
