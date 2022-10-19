import requests

from jobcoin.constants import API_ADDRESS_URL
from jobcoin.exceptions import (
    CheckAddressInUseException,
    InvalidWithdrawalAddressException,
    WithdrawalAddressInUseException,
)


def convert_input_to_withdrawal_addresses(input):
    withdrawal_addresses = input.split(",")
    withdrawal_addresses = [address.strip() for address in withdrawal_addresses]
    check_empty_addresses(withdrawal_addresses)
    check_addresses_in_use(withdrawal_addresses)
    return withdrawal_addresses


def check_empty_addresses(withdrawal_addresses):
    withdrawal_addresses_non_empty = [
        address for address in withdrawal_addresses if address
    ]
    if withdrawal_addresses != withdrawal_addresses_non_empty:
        raise InvalidWithdrawalAddressException()


def check_addresses_in_use(withdrawal_addresses):
    addresses_in_use = []
    for address in withdrawal_addresses:
        try:
            response = requests.get(f"{API_ADDRESS_URL}/{address}", timeout=1)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise CheckAddressInUseException(e.response.text)
        address_info = response.json()
        if address_info["balance"] != "0" or address_info["transactions"]:
            addresses_in_use.append(address)
    if addresses_in_use:
        addresses_in_use_str = ",".join(addresses_in_use)
        raise WithdrawalAddressInUseException(addresses_in_use_str)
