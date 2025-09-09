import time, random
from typing import List, Optional, Dict, Any
from core.block import Block
from core.crypto import hash_block

class HybridConsensus:
    """
    Hybrid consensus (stake + light PoW giả lập):
    - Leader được chọn dựa theo stake và height
    - Chỉ leader mới mine block, mất block_time_ms mili-giây
    - Sinh ticket deterministic từ (seed, height, leader)
    - Hash block dựa trên body + ticket
    """

    def __init__(self, node_id: int, config: Dict[str, Any]):
        self.node_id = node_id
        self.config = config
        self.stakes = list(config.get("stakes", [100, 100, 100, 100, 100]))
        self.seed = int(config.get("seed", 0))
        self.block_time_ms = int(config.get("block_time_ms", 300))

    def _leader_for_height(self, h: int) -> int:
        total = sum(self.stakes)
        idx = (h * 7919) % total
        s = 0
        for i, w in enumerate(self.stakes):
            s += w
            if idx < s:
                return i
        return 0

    def _ticket_for(self, height: int, leader: int) -> int:
        rnd = random.Random((self.seed << 20) ^ (height << 8) ^ (leader << 4))
        return rnd.randint(0, 2**32 - 1)

    def mine_block(self, bc, txs: list) -> Optional[Block]:
        leader = self._leader_for_height(bc.length())
        if leader != self.node_id:
            return None  # không phải lượt của mình

        time.sleep(self.block_time_ms / 1000.0)

        b = Block(
            height=bc.length(),
            prev_hash=bc.tip().hash,
            transactions=txs,
            timestamp=time.time(),
            proposer=self.node_id,
            nonce=0,
            extra={"leader": leader}
        )
        b.extra["ticket"] = self._ticket_for(b.height, leader)

        body = b.__dict__.copy()
        body["hash"] = ""
        b.hash = hash_block(body)
        return b

    def validate_block(self, block: Block) -> bool:
        expected_leader = self._leader_for_height(block.height)
        if block.proposer != expected_leader:
            print(f"[Node {self.node_id}] Reject block {block.height}: proposer {block.proposer} != expected {expected_leader}")
            return False

        expected_ticket = self._ticket_for(block.height, expected_leader)
        if block.extra.get("ticket") != expected_ticket:
            print(f"[Node {self.node_id}] Reject block {block.height}: ticket mismatch")
            return False

        body = block.__dict__.copy()
        body["hash"] = ""
        if hash_block(body) != block.hash:
            print(f"[Node {self.node_id}] Reject block {block.height}: invalid hash")
            return False

        return True

    def select_best(self, local_chain: List[Block], candidate_chain: List[Block]) -> List[Block]:
        if len(candidate_chain) != len(local_chain):
            return candidate_chain if len(candidate_chain) > len(local_chain) else local_chain
        # tie-breaker: chuỗi nào có tổng stake lớn hơn trong 10 block cuối sẽ thắng
        def score(chain):
            last = chain[-10:]
            return sum(self.stakes[b.proposer or 0] for b in last)
        return candidate_chain if score(candidate_chain) > score(local_chain) else local_chain
