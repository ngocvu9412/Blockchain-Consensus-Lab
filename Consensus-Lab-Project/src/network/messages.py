from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class Message:
    typ: str  # 'block' | 'tx' | 'chain_req' | 'chain_resp' | 'hello'
    data: Dict[str, Any]
