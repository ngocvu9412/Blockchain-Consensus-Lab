import time, random
from .scenarios import Scenario

class Simulator:
    def __init__(self, node, scenario: str = "delays", seed: int = 42, target_blocks: int = 10):
        self.node = node
        self.seed = seed
        self.target_blocks = target_blocks
        random.seed(seed)
        if scenario == "partition":
            self.scenario = Scenario(name="partition", delays_ms=(80, 250), partition=True)
        else:
            self.scenario = Scenario(name="delays", delays_ms=(50, 200), partition=False)

    def run(self):
        target_len = 1 + self.target_blocks  # tính cả genesis
        while self.node.bc.length() < target_len:
            self.node.tick()
            time.sleep(0.02)  # giảm một chút cho nhanh nhạy


    def step(self):
        time.sleep(0.05)

