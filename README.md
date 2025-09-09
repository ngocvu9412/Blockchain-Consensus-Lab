# Consensus Lab – Blockchain Simulator

This project is a **blockchain simulator** built for teaching and experimentation.  
It runs a small peer-to-peer network of 5 nodes that exchange blocks and transactions.  

Two consensus mechanisms are available:

- **Proof of Work (PoW)** – each node produces blocks after a delay (`block_time_ms`), forks are resolved with the longest-chain rule.  
- **Hybrid (Stake + Work)** – block proposers are chosen with probability proportional to their stake, and must still perform a lightweight simulated PoW before their block is valid.  

The simulator can run under two **network scenarios**:
1. **Delays** – messages are slowed down.  
2. **Partition** – the network splits into two groups temporarily, then reconnects.  

---

## Directory Structure

```
Consensus-Lab-Project/
├── src/
│   ├── core/
│   │   ├── block.py
│   │   ├── transaction.py
│   │   ├── blockchain.py
│   │   └── crypto.py
│   ├── consensus/
│   │   ├── base.py
│   │   ├── pow.py
│   │   └── hybrid.py
│   ├── network/
│   │   ├── messages.py
│   │   ├── socket_network.py
│   │   └── socket_node.py
│   └── simulator/
│       ├── simulator.py
│       └── scenarios.py
├── config/
│   ├── pow_config.json
│   └── hybrid_config.json
├── scripts/
│   ├── start_network.sh
│   ├── run_pow_delays.sh
│   ├── run_pow_partition.sh
│   ├── run_hybrid_delays.sh
│   └── run_hybrid_partition.sh
├── main.py
├── requirements.txt
└── README.md
```

---

## Setup

```bash
python -m venv .venv
# Linux/Mac
source .venv/bin/activate
# Windows PowerShell
.venv\Scripts\activate

pip install -r requirements.txt
```

---

## Running the Simulator

### Manual mode

Open 5 terminals (one for each node):

```bash
python main.py --node-id 0 --consensus pow --scenario delays --seed 42 --target-blocks 10
python main.py --node-id 1 --consensus pow --scenario delays --seed 42 --target-blocks 10
python main.py --node-id 2 --consensus pow --scenario delays --seed 42 --target-blocks 10
python main.py --node-id 3 --consensus pow --scenario delays --seed 42 --target-blocks 10
python main.py --node-id 4 --consensus pow --scenario delays --seed 42 --target-blocks 10
```

Change parameters to test other cases:

- `--consensus pow | hybrid` – choose consensus type  
- `--scenario delays | partition` – choose network scenario  
- `--seed <int>` – set random seed (deterministic execution)  
- `--target-blocks <int>` – stop after this many blocks (excluding genesis)  

Example: run Hybrid consensus with partition and a different seed:
```bash
python main.py --node-id 0 --consensus hybrid --scenario partition --seed 99 --target-blocks 12
```

---

### Script mode (Linux/Mac)

```bash
chmod +x scripts/*.sh

# PoW with delays (seed = 42)
./scripts/run_pow_delays.sh 42

# PoW with partition
./scripts/run_pow_partition.sh 42

# Hybrid with delays
./scripts/run_hybrid_delays.sh 42

# Hybrid with partition
./scripts/run_hybrid_partition.sh 42
```

---

## Logs & Output

- Each node writes logs to `logs/node_<id>.log`.  
- Logs contain events such as transaction creation, block creation, block acceptance/rejection, and chain switches.  

**Example log line:**
```json
{"ts": 1712591234.12, "node_id": 2, "event": "block_create", "data": {"height": 3, "h": "a9b3f21c"}}
{"ts": 1712591234.25, "node_id": 1, "event": "block_accept", "data": {"height": 3, "h": "a9b3f21c", "from_node": 2}}
```

---

## Config

- Config files live in `config/`:  
  - `pow_config.json`  
  - `hybrid_config.json`  

They define parameters such as block time, initial balances, stakes, and difficulty.  

---

## Network Topology

- 5 nodes: `node0`–`node4`  
- Default ports:  
  - Node 0 → 9000  
  - Node 1 → 9001  
  - Node 2 → 9002  
  - Node 3 → 9003  
  - Node 4 → 9004  

(See `socket_network.py` to change ports if needed).  

---

## Notes

- This is a **simulation**, not a production blockchain.  
- It demonstrates forks, finality, and consensus under unreliable networks.  
- Re-running with the same seed produces the same sequence of blocks and forks.  

---

## Example Experiments

1. **PoW with network delays (seed=42, 10 blocks)**  
   Observe occasional forks and resolution via longest-chain rule.  

2. **Hybrid with partition (seed=99, 12 blocks)**  
   Watch how stake influences leader election, and how forks are resolved after partitions heal.  
