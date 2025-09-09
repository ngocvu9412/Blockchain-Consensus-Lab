import argparse, json, time
import sys, os, json
import time
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
READY_FILE = "ready_nodes.txt"
DONE_FILE = "done_nodes.txt"

from network.socket_node import Node
from network.socket_network import DEFAULT_PORTS
from simulator.simulator import Simulator

def load_params(consensus: str):
    if consensus == "pow":
        p = json.load(open("config/pow_config.json"))
    else:
        p = json.load(open("config/hybrid_config.json"))
    return p

def load_config(consensus: str, seed: int, target_blocks: int = 10):
    base = os.path.dirname(__file__)
    if consensus == "pow":
        path = os.path.join(base, "config", "pow_config.json")
    elif consensus == "hybrid":
        path = os.path.join(base, "config", "hybrid_config.json")
    else:
        raise ValueError(f"Unknown consensus {consensus}")

    with open(path, "r") as f:
        cfg = json.load(f)

    cfg["seed"] = seed
    cfg["target_blocks"] = target_blocks
    return cfg

def mark_ready(node_id: int, total: int):
    with open(READY_FILE, "a") as f:
        f.write(f"{node_id}\n")

def wait_all_ready(total: int):
    while True:
        if os.path.exists(READY_FILE):
            with open(READY_FILE) as f:
                lines = {int(x.strip()) for x in f if x.strip()}
            if len(lines) >= total:
                break
        time.sleep(0.5)

def mark_done(node_id: int, total: int):
    with open(DONE_FILE, "a") as f:
        f.write(f"{node_id}\n")

def wait_all_done(total: int):
    while True:
        if os.path.exists(DONE_FILE):
            with open(DONE_FILE) as f:
                lines = {int(x.strip()) for x in f if x.strip()}
            if len(lines) >= total:
                break
        time.sleep(0.5)
    
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--node-id", type=int, required=True)
    parser.add_argument("--consensus", choices=["pow","hybrid"], required=True)
    parser.add_argument("--scenario", choices=["delays","partition"], required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--target-blocks", type=int, default=10)
    args = parser.parse_args()

    # load config JSON
    config = load_config(args.consensus, args.seed, args.target_blocks)

    # peers = tất cả port trừ node hiện tại
    peers = [p for i, p in enumerate(DEFAULT_PORTS) if i != args.node_id]

    # log_path
    log_path = os.path.join("logs", f"node_{args.node_id}.log")
    os.makedirs("logs", exist_ok=True)

    # tạo node
    node = Node(
        args.node_id,
        args.consensus,
        config,
        peers,
        log_path
    )
    node.start()
    mark_ready(args.node_id, len(DEFAULT_PORTS))
    time.sleep(1.0)
    
    sim = Simulator(node, args.scenario, args.seed, args.target_blocks)
    node.scenario = sim.scenario
    sim.run()
    target_len = 1 + args.target_blocks
    try:
        while node.bc.length() < target_len:
            node.tick()
            sim.step()
    except KeyboardInterrupt:
        pass
    finally:
        # báo hiệu node đã xong
        mark_done(args.node_id, len(DEFAULT_PORTS))

        # chờ tất cả node khác cũng xong rồi mới stop
        wait_all_done(len(DEFAULT_PORTS))

        node.stop()

if __name__ == "__main__":
    main()


