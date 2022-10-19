import datetime
import logging
import uuid
from typing import Dict

import requests

from jobcoin.account import Account
from jobcoin.constants import (
    API_ADDRESS_URL,
    API_TRANSACTIONS_URL,
    FIRST_WITHDRAWAL_ADDRESS_INDEX,
    HOUSE_ADDRESS,
    WITHDRAWAL_INCREMENT,
)


class JobCoinMixer:
    def __init__(self) -> None:
        self.deposit_address_store: Dict[str, Account] = {}

    def get_new_deposit_address(self, withdrawal_addresses):
        new_address = "deposit_address_" + uuid.uuid4().hex
        self.deposit_address_store[new_address] = Account(
            withdrawal_addresses=withdrawal_addresses,
        )
        logging.info(
            f"New {new_address} for withdrawal addresses {withdrawal_addresses}"
        )
        return new_address

    def get_new_deposits(self, offset):
        for deposit_address in self.deposit_address_store.keys():
            try:
                response = requests.get(
                    f"{API_ADDRESS_URL}/{deposit_address}", timeout=1
                )
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                logging.info(
                    f"Error getting deposit address info {deposit_address}: {e.response.text}"
                )
                continue

            transactions = response.json()["transactions"]
            for transaction in transactions[::-1]:
                if self._should_process_transaction(
                    transaction, offset, deposit_address
                ):
                    if self.transfer_to_house_address(
                        transaction["toAddress"], transaction["amount"]
                    ):
                        self.deposit_address_store[
                            transaction["toAddress"]
                        ].total_amount += float(transaction["amount"])

    def distribute_deposits(self):
        for _, account in self.deposit_address_store.items():
            withdrawl_amount = (
                account.withdrawal_amount
                if account.withdrawal_amount < account.total_amount
                else account.total_amount
            )
            if not withdrawl_amount:
                continue
            if self.transfer_to_withdrawal_address(
                account.withdrawal_addresses[account.withdrawal_addresses_index],
                withdrawl_amount,
            ):
                account.total_amount -= withdrawl_amount
                account.withdrawal_addresses_index = (
                    account.withdrawal_addresses_index + 1
                ) % len(account.withdrawal_addresses)
                if account.withdrawal_addresses_index == FIRST_WITHDRAWAL_ADDRESS_INDEX:
                    account.withdrawal_amount += WITHDRAWAL_INCREMENT

    def transfer_to_house_address(self, from_address, amount):
        return self._send_jobcoins(from_address, HOUSE_ADDRESS, amount)

    def transfer_to_withdrawal_address(self, to_address, amount):
        return self._send_jobcoins(HOUSE_ADDRESS, to_address, amount)

    def _send_jobcoins(self, from_address, to_address, amount):
        try:
            response = requests.post(
                API_TRANSACTIONS_URL,
                data={
                    "fromAddress": from_address,
                    "toAddress": to_address,
                    "amount": str(amount),
                },
                timeout=1,
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logging.info(
                f"Error transferring {amount} from {from_address} to {to_address}: {e.response.text}."
            )
            return False
        else:
            logging.info(f"Transfered {amount} from {from_address} to {to_address}.")
            return True

    def _should_process_transaction(self, transaction, offset, deposit_address):
        return (
            self._is_after_offset(transaction["timestamp"], offset)
            and transaction["toAddress"] == deposit_address
        )

    def _is_after_offset(self, timestamp, offset):
        transaction_time = datetime.datetime.strptime(
            timestamp, "%Y-%m-%dT%H:%M:%S.%f%z"
        ).replace(tzinfo=None)
        return transaction_time >= offset


jobcoin_mixer = JobCoinMixer()
