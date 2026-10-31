"""Deterministic Messaging Policy Engine (BRD MOD-07A, system design §3 / §5.2).

The LLM never decides whether a message may be sent; every outbound goes through `evaluate`.
"""

from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

POLICY_VERSION = "2026.10.1"
STANDARD_WINDOW = timedelta(hours=24)

# Purposes: response (reply inside window), quiet_ack (static night template),
# follow_up (scheduled care inside window), marketing (needs Marketing Messages opt-in).
PURPOSES = ("response", "quiet_ack", "follow_up", "marketing")


@dataclass(frozen=True)
class ActiveHours:
    tz: str
    start: str  # "08:00"
    end: str  # "22:00"

    def _bounds(self) -> tuple[time, time]:
        return time.fromisoformat(self.start), time.fromisoformat(self.end)

    def is_active(self, now: datetime) -> bool:
        start, end = self._bounds()
        local = now.astimezone(ZoneInfo(self.tz)).time()
        if start <= end:
            return start <= local < end
        return local >= start or local < end  # window crossing midnight

    def next_start(self, now: datetime) -> datetime:
        """Next moment the active window opens (strictly after `now` if currently quiet)."""
        start, _ = self._bounds()
        local = now.astimezone(ZoneInfo(self.tz))
        candidate = local.replace(hour=start.hour, minute=start.minute, second=0, microsecond=0)
        if candidate <= local:
            candidate += timedelta(days=1)
        return candidate.astimezone(now.tzinfo)


@dataclass
class PolicyInput:
    now: datetime
    hours: ActiveHours
    purpose: str
    actor: str  # ai | human | system
    last_customer_message_at: datetime | None
    opted_out: bool = False
    marketing_opt_in: bool = False
    automation_paused: bool = False


@dataclass
class PolicyResult:
    decision: str  # ALLOW | HOLD | SKIP
    reasons: list[str] = field(default_factory=list)
    hold_until: datetime | None = None


def evaluate(p: PolicyInput) -> PolicyResult:
    if p.purpose not in PURPOSES:
        return PolicyResult("SKIP", ["unknown_purpose"])
    if p.opted_out:
        return PolicyResult("SKIP", ["customer_opted_out"])
    if p.actor != "human" and p.automation_paused:
        return PolicyResult("SKIP", ["automation_paused"])

    in_window = (
        p.last_customer_message_at is not None
        and p.now - p.last_customer_message_at < STANDARD_WINDOW
    )
    if p.purpose == "marketing":
        if not p.marketing_opt_in:
            return PolicyResult("SKIP", ["marketing_opt_in_required"])
    elif not in_window:
        return PolicyResult("SKIP", ["outside_24h_window"])

    # Humans may answer at night; automated sends wait for the active window.
    if p.actor != "human" and p.purpose != "quiet_ack" and not p.hours.is_active(p.now):
        return PolicyResult("HOLD", ["quiet_hours"], p.hours.next_start(p.now))
    return PolicyResult("ALLOW", ["ok"])
