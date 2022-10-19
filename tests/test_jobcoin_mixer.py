import datetime
from dataclasses import asdict
from unittest import TestCase
from unittest.mock import MagicMock, call, patch

import requests
from jobcoin.constants import (
    API_TRANSACTIONS_URL,
    FIRST_WITHDRAWAL_ADDRESS_INDEX,
    HOUSE_ADDRESS,
    WITHDRAWAL_INCREMENT,
)
from jobcoin.jobcoin_mixer import JobCoinMixer


@patch("jobcoin.jobcoin_mixer.requests.post")
@patch("jobcoin.jobcoin_mixer.requests.get")
class TestJobCoinMixer(TestCase):
    def setUp(self):
        self.mixer = JobCoinMixer()
        self.withdrawal_addresses_1 = ["a1", "a2"]
        self.withdrawal_addresses_2 = ["b1", "b2", "b3"]
        self.deposit_address_1 = self.mixer.get_new_deposit_address(
            self.withdrawal_addresses_1
        )
        self.deposit_address_2 = self.mixer.get_new_deposit_address(
            self.withdrawal_addresses_2
        )
        self.mock_amount = "50"

    def test_get_new_deposit_address(self, mock_get, mock_post):
        self.assertEqual(
            list(self.mixer.deposit_address_store.keys()),
            [self.deposit_address_1, self.deposit_address_2],
        )
        self.assertEqual(
            asdict(self.mixer.deposit_address_store[self.deposit_address_1]),
            {
                "withdrawal_addresses": self.withdrawal_addresses_1,
                "total_amount": 0,
                "withdrawal_amount": WITHDRAWAL_INCREMENT,
                "withdrawal_addresses_index": FIRST_WITHDRAWAL_ADDRESS_INDEX,
            },
        )

    def test_get_new_deposits_success(self, mock_get, mock_post):
        mock_get.return_value = self._get_mock_response(
            self._get_address_info(None, self.deposit_address_1)
        )
        offset = datetime.datetime(2022, 10, 13, 3, 17, 30)
        self.mixer.get_new_deposits(offset)
        self.assertEqual(
            self.mixer.deposit_address_store[self.deposit_address_1].total_amount,
            int(self.mock_amount),
        )
        mock_post.assert_called_once_with(
            API_TRANSACTIONS_URL,
            data=self._get_post_data(
                self.deposit_address_1, HOUSE_ADDRESS, self.mock_amount
            ),
            timeout=1,
        )

    def test_get_new_deposits_http_error(self, mock_get, mock_post):
        mock_get.return_value = self._get_mock_response(
            raise_for_status=requests.HTTPError(response=MagicMock(text="blah"))
        )
        offset = datetime.datetime(2022, 10, 13, 3, 17, 30)
        self.mixer.get_new_deposits(offset)
        self.assertEqual(
            self.mixer.deposit_address_store[self.deposit_address_1].total_amount,
            0,
        )

    def test_get_new_deposits_ignore_transactions_before_offset(
        self, mock_get, mock_post
    ):
        mock_get.return_value = self._get_mock_response(
            self._get_address_info(None, self.deposit_address_1)
        )
        offset = datetime.datetime(2022, 10, 13, 3, 17, 32)
        self.mixer.get_new_deposits(offset)
        self.assertEqual(
            self.mixer.deposit_address_store[self.deposit_address_1].total_amount,
            0,
        )
        mock_post.assert_not_called()

    def test_get_new_deposits_ignore_outgoing_transactions(self, mock_get, mock_post):
        mock_get.return_value = self._get_mock_response(
            self._get_address_info(self.deposit_address_1, HOUSE_ADDRESS)
        )
        offset = datetime.datetime(2022, 10, 13, 3, 17, 30)
        self.mixer.get_new_deposits(offset)
        self.assertEqual(
            self.mixer.deposit_address_store[self.deposit_address_1].total_amount,
            0,
        )
        mock_post.assert_not_called()

    def test_distribute_deposits_success(self, mock_get, mock_post):
        self.mixer.deposit_address_store[self.deposit_address_1].total_amount = int(
            self.mock_amount
        )
        self.mixer.deposit_address_store[self.deposit_address_2].total_amount = int(
            self.mock_amount
        )
        self.mixer.distribute_deposits()
        self.assertEqual(mock_post.call_count, 2)
        self.assertEqual(
            self.mixer.deposit_address_store[
                self.deposit_address_1
            ].withdrawal_addresses_index,
            1,
        )
        self.assertEqual(
            self.mixer.deposit_address_store[self.deposit_address_1].total_amount,
            int(self.mock_amount) - WITHDRAWAL_INCREMENT,
        )
        self.assertEqual(
            mock_post.call_args_list,
            [
                call(
                    API_TRANSACTIONS_URL,
                    data=self._get_post_data(
                        HOUSE_ADDRESS,
                        self.withdrawal_addresses_1[0],
                        WITHDRAWAL_INCREMENT,
                    ),
                    timeout=1,
                ),
                call(
                    API_TRANSACTIONS_URL,
                    data=self._get_post_data(
                        HOUSE_ADDRESS,
                        self.withdrawal_addresses_2[0],
                        WITHDRAWAL_INCREMENT,
                    ),
                    timeout=1,
                ),
            ],
        )

    def test_distribute_deposits_zero_balance(self, mock_get, mock_post):
        self.mixer.distribute_deposits()
        mock_post.assert_not_called()

    def test_distribute_deposits_distribute_remaining_balance_if_less_than_increment(
        self, mock_get, mock_post
    ):
        self.mixer.deposit_address_store[self.deposit_address_1].total_amount = 0.1
        self.mixer.distribute_deposits()
        mock_post.assert_called_once_with(
            API_TRANSACTIONS_URL,
            data=self._get_post_data(
                HOUSE_ADDRESS, self.withdrawal_addresses_1[0], "0.1"
            ),
            timeout=1,
        )

    def _get_mock_response(self, response_json=None, raise_for_status=None):
        mock_response = MagicMock()
        if raise_for_status:
            mock_response.raise_for_status = MagicMock()
            mock_response.raise_for_status.side_effect = raise_for_status
        else:
            mock_response.status_code = 200
            mock_response.json.return_value = response_json
        return mock_response

    def _get_address_info(self, from_address, to_address):
        return {
            "balance": self.mock_amount,
            "transactions": [self._get_transaction(from_address, to_address)],
        }

    def _get_transaction(self, from_address, to_address):
        return {
            "timestamp": "2022-10-13T03:17:31.170Z",
            "fromAddress": from_address,
            "toAddress": to_address,
            "amount": self.mock_amount,
        }

    def _get_post_data(self, from_address, to_address, amount):
        return {
            "fromAddress": from_address,
            "toAddress": to_address,
            "amount": str(amount),
        }
