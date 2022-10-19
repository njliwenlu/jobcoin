from unittest import TestCase
from unittest.mock import MagicMock, patch

import requests
from jobcoin.exceptions import (
    CheckAddressInUseException,
    InvalidWithdrawalAddressException,
    WithdrawalAddressInUseException,
)
from jobcoin.utils import convert_input_to_withdrawal_addresses


class TestUtils(TestCase):
    @patch("jobcoin.utils.requests.get")
    def test_valid_input(self, mock_get):
        mock_get.return_value = self._get_mock_response(
            {
                "balance": "0",
                "transactions": [],
            }
        )
        addresses = convert_input_to_withdrawal_addresses("a1,a2, a3")
        self.assertEqual(addresses, ["a1", "a2", "a3"])

    def test_empty_address(self):
        with self.assertRaises(InvalidWithdrawalAddressException):
            convert_input_to_withdrawal_addresses("a1,a2,")

    @patch("jobcoin.utils.requests.get")
    def test_addresses_in_use(self, mock_get):
        mock_get.return_value = self._get_mock_response(
            {
                "balance": "1",
                "transactions": ["test"],
            }
        )
        with self.assertRaises(WithdrawalAddressInUseException):
            convert_input_to_withdrawal_addresses("a1,a2")

    @patch("jobcoin.utils.requests.get")
    def test_request_exception(self, mock_get):
        mock_get.return_value = self._get_mock_response(
            raise_for_status=requests.HTTPError(response=MagicMock(text="blah"))
        )
        with self.assertRaises(CheckAddressInUseException):
            convert_input_to_withdrawal_addresses("a1,a2")

    def _get_mock_response(self, response_json=None, raise_for_status=None):
        mock_response = MagicMock()
        if raise_for_status:
            mock_response.raise_for_status = MagicMock()
            mock_response.raise_for_status.side_effect = raise_for_status
        else:
            mock_response.status_code = 200
            mock_response.json.return_value = response_json
        return mock_response
