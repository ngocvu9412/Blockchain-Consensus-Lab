import time, random
from typing import List, Optional, Dict, Any
from core.block import Block
from core.crypto import hash_block

class PoWConsensus:
    """
    Simulated PoW (no brute-force):
    - Mỗi block mất block_time_ms mili-giây để 'mine'
    - Sinh ticket deterministic từ (seed, height, node_id)
    - Hash block dựa trên body + ticket
    """

    def __init__(self, node_id: int, config: Dict[str, Any]):
        self.node_id = node_id
        self.config = config
        self.seed = int(config.get("seed", 0))
        self.block_time_ms = int(config.get("block_time_ms", 500))

    def _ticket_for(self, height: int) -> int:
        rng = random.Random(self.seed + height)
        val = rng.randint(0, 2**32 - 1)
        return val

    def mine_block(self, bc, txs: list) -> Block:
        # simulate mining delay
        time.sleep(self.block_time_ms / 1000.0)

        b = Block(
            height=bc.length(),
            prev_hash=bc.tip().hash,
            transactions=txs,
            timestamp=time.time(),
            proposer=self.node_id,
            nonce=0,
            extra={}
        )
        b.extra["ticket"] = self._ticket_for(b.height)

        body = b.__dict__.copy()
        body["hash"] = ""
        b.hash = hash_block(body)
        return b

    def validate_block(self, block: Block) -> bool:
        expected = self._ticket_for(block.height)
        actual = block.extra.get("ticket")
        if actual != expected:
            print(f"[Node {self.node_id}] FAIL ticket h={block.height}, expected={expected}, got={actual}")
            return False

        body = block.__dict__.copy()
        body["hash"] = ""
        recomputed = hash_block(body)
        if recomputed != block.hash:
            print(f"[Node {self.node_id}] FAIL hash h={block.height}, expected={block.hash}, got={recomputed}")
            return False
        
        return True

    def select_best(self, local_chain: List[Block], candidate_chain: List[Block]) -> List[Block]:
        return candidate_chain if len(candidate_chain) > len(local_chain) else local_chain
