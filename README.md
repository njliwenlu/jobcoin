# Jobcoin

This simple solution uses threads to run two periodic tasks in the background:
1. check for new deposits made into available deposit addresses and transfer deposits to house address
2. distribute corresponding amount from house address to withdrawal addresses set for each deposit address in small discrete increments

This solution stores deposit addresses created for each input of withdrawal addresses in memory, runs when the CLI tool starts and ends when CLI tool stops, meaning no more periodic tasks and all information stored in memory are lost (e.g. deposit address to withdrawal addresses mapping, any remaining amount to be distributed for deposit addresses).

Assume multiple deposits can be made to an deposit address and only new deposits should be transfered to house address, this solution uses an offset to track the last time a check has been performed and only process newer transactions after the last poll. Also, this solution ignores any outgoing transactions happened in a deposit address and only act on incoming transactions, which it transfers the amount to house address.

The way this solution handles any potential HTTP error is by simply log and ignore. It attempts to try to again next time this periodic task runs. A more robust solution would be add retry with expenantial backoff for each http request, and also alerting on elevated error rate.

A better solution would be to write a Flask app that uses Celery for periodic tasks and sqlalchemy for managing database persistence. This Flask app serves a /create_deposit_address endpoint that accepts POST request from the CLI tool so that there is a new JobCoinMixer service that CLI tool can talk to. Usage of the CLI tool and the running of the JobCoinMixer are independent from each other. The JobCoinMixer service persists deposit addresses created to a database along with additional information (e.g. withdrawal_addresses, total_amount, withdrawal_amount, withdrawal_address_index). Each time a get_new_deposits Celery task runs, it updates the total_amount for each deposit addresses with new coins. Each time a distribute_deposits Celery task runs, it updates fields accordingly (i.e. decrement total_amount, increase withdrawal_amount, increase withdrawal_address_index). A more robust way to handle offset would be to store the last checked deposit timestamp for each deposit address in the DB as well so that when the service accidentally stops, it can catch up on all new deposits made since teh last checked deposit timestamp.


## Setup
1. Virtual environment
```
python3 -m venv venv
. venv/bin/activate
pip3 install -r requirements-dev.txt
```

## Testing:
1. Run all tests
```
python -m pytest -v
```
2. Check code coverage
```
python -m pytest --cov-report term-missing --cov=jobcoin
```
