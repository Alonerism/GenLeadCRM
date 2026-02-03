import uuid


def new_id(prefix: str) -> str:
    # Keep it human-parseable + globally unique.
    return f"{prefix}_{uuid.uuid4().hex}"








