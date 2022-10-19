#!/usr/bin/env python
import sys
from threading import Thread

import click

from jobcoin.exceptions import (
    CheckAddressInUseException,
    InvalidWithdrawalAddressException,
    WithdrawalAddressInUseException,
)
from jobcoin.jobcoin_mixer import jobcoin_mixer
from jobcoin.tasks import distribute_deposits, get_new_deposits
from jobcoin.utils import convert_input_to_withdrawal_addresses


def start_background_tasks():
    thread1 = Thread(target=get_new_deposits, daemon=True)
    thread2 = Thread(target=distribute_deposits, daemon=True)
    thread1.start()
    thread2.start()
    return [thread1, thread2]


@click.command()
def main(args=None):
    print("Welcome to the Jobcoin mixer!\n")
    tasks = start_background_tasks()

    while True:
        addresses = click.prompt(
            "Please enter a comma-separated list of new, unused Jobcoin "
            "addresses where your mixed Jobcoins will be sent.",
            prompt_suffix="\n[blank to quit] > ",
            default="",
            show_default=False,
        )
        if addresses.strip() == "":
            sys.exit(0)

        try:
            withdrawal_addresses = convert_input_to_withdrawal_addresses(addresses)
        except (
            InvalidWithdrawalAddressException,
            CheckAddressInUseException,
            WithdrawalAddressInUseException,
        ) as e:
            click.echo(e)
        else:
            deposit_address = jobcoin_mixer.get_new_deposit_address(
                withdrawal_addresses
            )
            click.echo(
                "\nYou may now send Jobcoins to address {deposit_address} They "
                "will be mixed and sent to your destination addresses.\n".format(
                    deposit_address=deposit_address
                )
            )


if __name__ == "__main__":
    sys.exit(main())
