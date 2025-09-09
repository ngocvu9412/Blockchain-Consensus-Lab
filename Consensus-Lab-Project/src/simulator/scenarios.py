from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class Scenario:
    name: str
    delays_ms: Tuple[int,int] = (50, 200)     # not fully enforced in this minimal demo
    partition: bool = False                   # flag only; demo keeps simple
