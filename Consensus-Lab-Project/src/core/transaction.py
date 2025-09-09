from dataclasses import dataclass

@dataclass
class Transaction:
    sender: int
    receiver: int
    amount: int
