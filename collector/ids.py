import uuid

NAMESPACE = uuid.UUID("d7e7b4d9-f5b8-5ce1-90bc-7f3e4ae0cb02")

def public_id(*parts: str) -> str:
    normalized = "|".join(" ".join(str(p).strip().lower().split()) for p in parts)
    return str(uuid.uuid5(NAMESPACE, normalized))
