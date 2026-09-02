from datetime import datetime, timezone


def utcnow() -> datetime:
    """Current UTC time as a naive datetime.

    Every datetime in this codebase — model columns, analytics inputs and
    outputs — is naive and implicitly UTC. SQLite (used in tests) silently
    drops tzinfo on read, so mixing naive and aware datetimes raises
    TypeError the moment two get compared; rather than patch that per
    dialect, the whole app picks one convention and holds it. Never attach
    tzinfo to a datetime that flows through this codebase — convert at the
    boundary (e.g. an API client sending an ISO string with an offset)
    instead."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
