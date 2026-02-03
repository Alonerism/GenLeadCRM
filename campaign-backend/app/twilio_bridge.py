from __future__ import annotations

import os
from typing import Any, Optional, TYPE_CHECKING


class TwilioConfigError(RuntimeError):
    pass


if TYPE_CHECKING:
    # Only for type-checkers; Twilio is optional at runtime (no real calling in dev).
    from twilio.rest import Client  # pragma: no cover


def _get_twilio_client():
    """
    Return a Twilio REST client, or raise TwilioConfigError if Twilio isn't usable.

    Twilio is intentionally optional in this repo so the backend can run end-to-end
    without real calling / credentials.
    """
    try:
        from twilio.rest import Client  # type: ignore
    except ModuleNotFoundError as e:
        raise TwilioConfigError("Twilio SDK not installed. Install with `pip install twilio` (or `pip install -r requirements.txt`).") from e

    sid = os.getenv("TWILIO_ACCOUNT_SID", "").strip()
    token = os.getenv("TWILIO_AUTH_TOKEN", "").strip()
    if not sid or not token:
        raise TwilioConfigError("Twilio not configured (set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN).")
    return Client(sid, token)


def _get_from_number() -> str:
    v = os.getenv("TWILIO_FROM_NUMBER", "").strip()
    if not v:
        raise TwilioConfigError("Missing TWILIO_FROM_NUMBER.")
    return v


def start_outbound_call(*, to_number: str, twiml_url: str, status_callback_url: str, status_callback_events: Optional[list[str]] = None, extra_params: Optional[dict[str, Any]] = None) -> str:
    """
    Creates an outbound call in Twilio, returning CallSid.
    """
    client = _get_twilio_client()
    from_number = _get_from_number()

    events = status_callback_events or ["initiated", "ringing", "answered", "completed"]

    call = client.calls.create(
        to=to_number,
        from_=from_number,
        url=twiml_url,
        status_callback=status_callback_url,
        status_callback_event=events,
        status_callback_method="POST",
        machine_detection="Enable",
        **(extra_params or {}),
    )
    return str(call.sid)


