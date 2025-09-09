import json, time, threading, random, os, sys
from typing import List, Dict, Any, Optional
from src.core.block import Block
from core.blockchain import Blockchain
from consensus.pow import PoWConsensus
from consensus.hybrid import HybridConsensus
from .socket_network import Server, send_json, DEFAULT_PORTS

class Node:
    scenario: Any = None
    def __init__(self, node_id: int, consensus: str, config: Dict[str, Any], peers: List[int], log_path: str):
        self.node_id = node_id
        self.consensus_name = consensus
        self.config = config
        self.peers = peers
        self.log_path = log_path
        self.bc = Blockchain(initial_balances=config.get("initial_balances"))
        self.bc.genesis()
        self.mempool: List[dict] = []
        self.last_broadcast = 0
        self.server = Server(DEFAULT_PORTS[node_id], self.on_message)
        if consensus == 'pow':
            self.cons = PoWConsensus(self.node_id, self.config)
        else:
            self.cons = HybridConsensus(self.node_id, self.config)

        # invariants
        self.k_final = int(config.get("finality_depth", 4))
        self.finalized_map: Dict[int, str] = {}  # height -> hash
        self.finalized_height: int = -1
        print(f"[DEBUG] Node {self.node_id} peers = {self.peers}")
        os.makedirs(os.path.dirname(log_path), exist_ok=True)

    def log(self, event_type: str, **data):
        entry = {"ts": time.time(), "node_id": self.node_id, "event": event_type, "data": data}
        with open(self.log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def start(self):
        print(f"[DEBUG][Node {self.node_id}] Seed = {int(self.config.get('seed', 0))}")
        if getattr(self, "_started", False):
            return
        self.server.start()
        self._started = True
        self.log("start", consensus=self.consensus_name)
        self.log("peers_init", peers=self.peers)


    def stop(self):
        self.server.stop()

    def connect_peers(self):
        # announce ourselves
        for p in self.peers:
            self._send(p, {"typ":"hello","data":{"from": self.node_id}})

    def _send(self, port: int, obj: dict):
        try:
            # Delay nếu có
            if hasattr(self, "scenario") and self.scenario and self.scenario.delays_ms:
                import time, random
                dmin, dmax = self.scenario.delays_ms
                time.sleep(random.uniform(dmin, dmax) / 1000.0)

            # Partition nếu có
            if hasattr(self, "scenario") and self.scenario and self.scenario.partition:
                g1 = {0, 1}
                g2 = {2, 3, 4}
                if (self.node_id in g1 and port in [9002, 9003, 9004]) or \
                (self.node_id in g2 and port in [9000, 9001]):
                    self.log("send_drop", peer=port, typ=obj.get("typ"))
                    return  # message bị drop

            # Gửi thật sự
            send_json("127.0.0.1", port, obj)
            
        except Exception as e:
            self.log("send_fail", peer=port, error=str(e))

    def broadcast_block(self, b: Block):
        for p in self.peers:
            self._send(p, {"typ":"block","data":{"block": b.__dict__}})

    def ask_chain(self, pid: int):
        self._send(pid, {"typ":"chain_req","data":{"from": self.node_id}})

    # ------------- Transactions -------------
    def maybe_create_tx(self):
        """Occasionally create a small tx from this node to a random peer."""
        if random.random() < 0.25:  # 25% chance per tick
            targets = [p for p in range(len(DEFAULT_PORTS)) if p != self.node_id]
            if not targets:
                return
            receiver = random.choice(targets)
            balance = self.bc.balances.get(self.node_id, 0)
            if balance <= 1:
                return
            amount = max(1, balance // random.randint(10, 20))  # small amount
            tx = {"sender": self.node_id, "receiver": receiver, "amount": amount}
            self.mempool.append(tx)
            self.log("tx_create", **tx)

    # ------------- Invariants -------------
    def _check_invariants(self):
        # finality increases, no two final blocks at same height
        fb = self.bc.k_final(self.k_final)
        if fb is not None:
            h = fb.height
            hh = fb.hash
            # rule 1: final height only increases
            if h < self.finalized_height:
                self.log("invariant_fail", reason="final_height_decrease", h=h)
                sys.exit(1)
            # rule 2: no two different finals at same height
            prev = self.finalized_map.get(h)
            if prev is not None and prev != hh:
                self.log("invariant_fail", reason="two_final_blocks_same_height", h=h)
                sys.exit(1)
            # record
            self.finalized_map[h] = hh
            self.finalized_height = max(self.finalized_height, h)

    def on_message(self, obj: dict):        
        # unwrap nếu có 'raw'
        if "raw" in obj:
            self.log("raw_recv", typ=obj.get("typ"), raw=obj)
            obj = obj["raw"]

        typ = obj.get("typ")
        data = obj.get("data", {})
            
        if typ == "hello":
            self.log("hello", **data)

        elif typ == "block":
            bdict = data.get("block", {})
            if not bdict:
                self.log("debug_block_empty", raw=obj)  # log để kiểm tra
                return
            b = Block(**bdict)

            if self.cons.validate_block(b):
                # Case 1: nối tiếp tip local
                if b.height == self.bc.length() and b.prev_hash == self.bc.tip().hash:
                    if self.bc.add_block(b):
                        self.mempool = [tx for tx in self.mempool if tx not in b.transactions]
                        self.log("block_accept", height=b.height, h=b.hash[:8], from_node=b.proposer)
                        self._check_invariants()
                    else:
                        self.log("block_add_fail", height=b.height, prev=b.prev_hash[:8], tip=self.bc.tip().hash[:8])

                # Case 2: block đi xa hơn chain local
                elif b.height > self.bc.length():
                    sender = b.proposer
                    peer_port = DEFAULT_PORTS[sender]  # ánh xạ node_id -> port
                    self.log("block_out_of_sync", height=b.height, from_node=sender)
                    self.ask_chain(peer_port)

                # Case 3: block cùng height nhưng prev không khớp
                else:
                    sender = b.proposer
                    peer_port = DEFAULT_PORTS[sender]  # đổi node_id sang port
                    self.log("block_reject", height=b.height, reason="bad_prev", from_node=sender)
                    self.ask_chain(peer_port)

            else:
                self.log("block_reject", height=b.height, reason="invalid_block")

        elif typ == "chain_req":
            chain = [blk.__dict__ for blk in self.bc.chain]
            from_id = data.get("from", 0)
            self._send(DEFAULT_PORTS[from_id], {"typ": "chain_resp", "data": {"chain": chain}})

        elif typ == "chain_resp":
            chain_dicts = data.get("chain", [])
            cand = [Block(**d) for d in chain_dicts]

            # chọn chain tốt nhất
            best = self.cons.select_best(self.bc.chain, cand)

            if best is cand and len(cand) > len(self.bc.chain):
                self.bc.chain = cand
                self.bc.rebuild_state()
                self.log("chain_switch", new_len=len(cand))
                self._check_invariants()

    def tick(self):
        now_ms = int(time.time() * 1000)

        # tạo tx ngẫu nhiên
        self.maybe_create_tx()

        # Gọi mine_block theo loại consensus
        mem = self.mempool[:5]
        b = self.cons.mine_block(self.bc, mem)  # PoW trả về Block, Hybrid có thể trả None
        if b:
            ok = self.bc.add_block(b)
            if ok:
                self.mempool = [tx for tx in self.mempool if tx not in b.transactions]
                self.log("block_create", height=b.height, h=b.hash[:8])
                self.broadcast_block(b)
                self._check_invariants()

        # đôi khi sync
        if now_ms - self.last_broadcast > 1500:
            peer = random.choice(self.peers) if self.peers else None
            if peer is not None:
                self.ask_chain(peer)
            self.last_broadcast = now_ms
            
        if self.bc.length() >= 1 + self.config.get("target_blocks", 10):
            return  # không mine thêm
    def start_mining(self):
        while True:
            txs = self.mempool[:]  # copy txs từ mempool
            height = self.bc.length()

            if isinstance(self.cons, HybridConsensus):
                leader = self.cons._leader_for_height(height)
                if leader != self.node_id:
                    # không phải leader, đợi cho đến block tiếp theo
                    time.sleep(self.cons.block_time_ms / 1000.0)
                    continue

            # gọi consensus để tạo block
            block = self.cons.mine_block(self.bc, txs)

            # log + broadcast
            self.log("block_create", height=block.height, h=block.hash[:8])
            self.broadcast_block(block)

            # xóa txs đã included
            self.mempool = [tx for tx in self.mempool if tx not in block.transactions]

            time.sleep(self.cons.block_time_ms / 1000.0)


