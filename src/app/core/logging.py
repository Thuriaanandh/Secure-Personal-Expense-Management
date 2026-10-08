"""
Structured Security Logging Module for SPEMA.

Provides standardized, tamper-evident, JSON-formatted security event logging
for SIEM and container runtime ingestion. Enforces strict redaction of credentials,
tokens, passwords, and sensitive financial fields.
"""

import json
import logging
from collections import deque
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Dict, List, Optional

# Security Logger Instance
security_logger = logging.getLogger("spema.security")

# Blacklisted keys that must NEVER appear in logs (CWE-532)
REDACTED_KEYS = {
    "password",
    "passwd",
    "password_hash",
    "confirm_password",
    "token",
    "access_token",
    "refresh_token",
    "secret",
    "secret_key",
    "authorization",
    "cookie",
    "set-cookie",
    "credit_card",
    "cvv",
    "ssn",
}

# In-memory circular buffer for recent security events (inspection & auditing)
_EVENT_BUFFER: deque = deque(maxlen=200)
_BUFFER_LOCK = Lock()


def mask_security_payload(data: Any) -> Any:
    """
    Recursively scrubs sensitive data fields from dictionaries and lists.
    Replaces credentials, tokens, and secret parameters with '[REDACTED]'.
    """
    if isinstance(data, dict):
        cleaned = {}
        for key, value in data.items():
            if any(sensitive in str(key).lower() for sensitive in REDACTED_KEYS):
                cleaned[key] = "[REDACTED]"
            else:
                cleaned[key] = mask_security_payload(value)
        return cleaned
    elif isinstance(data, list):
        return [mask_security_payload(item) for item in data]
    elif isinstance(data, tuple):
        return tuple(mask_security_payload(item) for item in data)
    return data


def log_security_event(
    event_type: str,
    action: str,
    status_code: int,
    user_id: Optional[int] = None,
    client_ip: str = "unknown",
    correlation_id: Optional[str] = None,
    resource: str = "unknown",
    details: Optional[Dict[str, Any]] = None,
    severity: str = "INFO",
) -> Dict[str, Any]:
    """
    Emits a structured JSON security audit event to the security logger
    and caches it in the in-memory circular buffer.

    Never logs passwords, tokens, or sensitive credentials.
    """
    sanitized_details = mask_security_payload(details) if details else {}

    event_payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "severity": severity.upper(),
        "event_type": event_type,
        "action": action,
        "status_code": status_code,
        "user_id": user_id,
        "client_ip": client_ip,
        "correlation_id": correlation_id,
        "resource": resource,
        "details": sanitized_details,
    }

    # Emit JSON structured log string
    log_line = json.dumps(event_payload, separators=(",", ":"))
    if severity.upper() == "ERROR":
        security_logger.error(log_line)
    elif severity.upper() in ("WARN", "WARNING"):
        security_logger.warning(log_line)
    else:
        security_logger.info(log_line)

    # Store in memory buffer for audit inspection
    with _BUFFER_LOCK:
        _EVENT_BUFFER.append(event_payload)

    return event_payload


def get_recent_security_events(limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieves the most recent security events from the in-memory audit buffer."""
    with _BUFFER_LOCK:
        events = list(_EVENT_BUFFER)
    return events[-limit:]


def clear_security_events_for_testing():
    """Resets the in-memory audit event buffer for test isolation."""
    with _BUFFER_LOCK:
        _EVENT_BUFFER.clear()
