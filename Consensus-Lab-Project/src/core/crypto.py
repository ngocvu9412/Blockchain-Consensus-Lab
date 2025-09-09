import hashlib
import json

def _canonical(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(',',':')).encode()

def hash_block(block_dict: dict) -> str:
    body = _canonical(block_dict)
    return hashlib.sha256(body).hexdigest()

def meets_difficulty(h: str, difficulty: int) -> bool:
    return h.startswith('0' * max(0, difficulty))
