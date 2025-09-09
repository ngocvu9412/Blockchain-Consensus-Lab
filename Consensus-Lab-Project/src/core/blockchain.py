from __future__ import annotations
from typing import List, Dict, Optional
from .block import Block
from .crypto import hash_block

class Blockchain:
    """
    Account-based state:
      - balances: Dict[int, int]
      - apply_block(): validate & mutate balances
      - rebuild_state(): recompute balances from genesis + all blocks
    """

    def __init__(self, initial_balances: Optional[List[int]] = None):
        self.chain: List[Block] = []
        self.genesis_balances: List[int] = list(initial_balances or [1000, 1000, 1000, 1000, 1000])
        self.balances: Dict[int, int] = {i: bal for i, bal in enumerate(self.genesis_balances)}

    def genesis(self) -> Block:
        if self.chain:
            return
        g = Block(
            height=0,
            prev_hash="0" * 64,
            transactions=[],
            timestamp=0,        # FIXED timestamp để mọi node giống nhau
            proposer=-1,
            nonce=0,
            extra={}
        )
        g.hash = hash_block(g.__dict__)
        self.chain.append(g)
        print(f"[DEBUG][genesis] Genesis hash = {g.hash[:8]}")
        return g

    def tip(self) -> Block:
        return self.chain[-1]

    def length(self) -> int:
        return len(self.chain)

    def k_final(self, k: int) -> Optional[Block]:
        if len(self.chain) <= k:
            return None
        return self.chain[-(k+1)]

    # ---- State handling ----
    def _can_apply_tx(self, tx: dict) -> bool:
        sender = int(tx["sender"])
        receiver = int(tx["receiver"])
        amount = int(tx["amount"])
        if amount <= 0:
            return False
        if sender == receiver:
            return False
        if self.balances.get(sender, 0) < amount:
            return False
        return True

    def _apply_tx(self, tx: dict):
        sender = int(tx["sender"])
        receiver = int(tx["receiver"])
        amount = int(tx["amount"])
        self.balances[sender] -= amount
        self.balances[receiver] = self.balances.get(receiver, 0) + amount

    def apply_block(self, b: Block) -> bool:
        """
        Validate + apply transactions to balances.
        Double-spend is prevented by ensuring sender has enough at apply-time.
        If any tx invalid => whole block invalid.
        """
        snapshot = dict(self.balances)  # rollback if needed
        for tx in b.transactions:
            if not self._can_apply_tx(tx):
                self.balances = snapshot  # rollback
                return False
            self._apply_tx(tx)
        return True

    def add_block(self, block: Block) -> bool:
        # check prev
        if block.prev_hash != self.tip().hash:
            print("[DEBUG add_block] prev_hash mismatch")
            return False

        # check height
        if block.height != self.length():
            print(f"[DEBUG add_block] height mismatch: got {block.height}, expected {self.length()}")
            return False

        self.chain.append(block)
        return True

    def rebuild_state(self):
        """Recompute balances from genesis + all applied blocks."""
        self.balances = {i: bal for i, bal in enumerate(self.genesis_balances)}
        # skip genesis at index 0
        for b in self.chain[1:]:
            ok = self.apply_block(b)
            if not ok:
                # If rebuilding fails, we leave balances up to the last valid block
                # and stop there (caller may want to truncate chain, but here we just break).
                break

