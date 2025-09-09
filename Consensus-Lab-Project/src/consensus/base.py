from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from ..core.block import Block

class ConsensusAlgorithm(ABC):
    def __init__(self, node_id: int, params: Dict[str, Any]):
        self.node_id = node_id
        self.params = params

    @abstractmethod
    def can_propose_block(self, now_ms: int) -> bool: ...

    @abstractmethod
    def create_block(self, prev_block: Block, mempool: List[dict]) -> Optional[Block]: ...

    @abstractmethod
    def validate_block(self, block: Block) -> bool: ...

    @abstractmethod
    def select_best(self, local_chain: List[Block], candidate_chain: List[Block]) -> List[Block]: ...
