import datetime
import logging
import time

from jobcoin.constants import (
    DISTRIBUTE_DEPOSITS_INTERVAL_SEC,
    GET_NEW_DEPOSITS_INTERVAL_SEC,
)
from jobcoin.jobcoin_mixer import jobcoin_mixer


def get_new_deposits():
    global jobcoin_mixer
    while True:
        logging.info("[Task] get_new_deposits")
        offset = datetime.datetime.utcnow() - datetime.timedelta(
            seconds=GET_NEW_DEPOSITS_INTERVAL_SEC
        )
        jobcoin_mixer.get_new_deposits(offset)
        time.sleep(GET_NEW_DEPOSITS_INTERVAL_SEC)


def distribute_deposits():
    global jobcoin_mixer
    while True:
        logging.info("[Task] distribute_deposits")
        jobcoin_mixer.distribute_deposits()
        time.sleep(DISTRIBUTE_DEPOSITS_INTERVAL_SEC)
