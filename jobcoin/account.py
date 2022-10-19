from dataclasses import dataclass
from typing import List

from jobcoin.constants import FIRST_WITHDRAWAL_ADDRESS_INDEX, WITHDRAWAL_INCREMENT


@dataclass
class Account:
    withdrawal_addresses: List[str]
    total_amount: float = 0
    withdrawal_amount: int = WITHDRAWAL_INCREMENT
    withdrawal_addresses_index: int = FIRST_WITHDRAWAL_ADDRESS_INDEX
