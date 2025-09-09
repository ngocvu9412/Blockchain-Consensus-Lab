from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Block:
    height: int
    prev_hash: str
    transactions: List[dict]
    timestamp: float
    nonce: int = 0
    proposer: Optional[int] = None
    extra: dict = field(default_factory=dict)
    hash: str = ""  # set by crypto.hash_block

