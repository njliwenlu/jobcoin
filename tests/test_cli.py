import re
from unittest import TestCase
from unittest.mock import patch

from click.testing import CliRunner
from jobcoin import cli
from jobcoin.exceptions import WithdrawalAddressInUseException


class TestCli(TestCase):
    def test_cli_basic(self):
        runner = CliRunner()
        result = runner.invoke(cli.main)
        assert result.exit_code == 0
        assert "Welcome to the Jobcoin mixer" in result.output

    @patch(
        "jobcoin.cli.convert_input_to_withdrawal_addresses", return_value=["1234,4321"]
    )
    def test_cli_creates_address(self, mock_convert):
        runner = CliRunner()
        address_create_output = runner.invoke(cli.main, input="1234,4321").output
        output_re = re.compile(
            r"You may now send Jobcoins to address deposit_address_[0-9a-zA-Z]{32}. "
            "They will be mixed and sent to your destination addresses."
        )
        assert output_re.search(address_create_output) is not None

    @patch(
        "jobcoin.cli.convert_input_to_withdrawal_addresses",
        side_effect=WithdrawalAddressInUseException("1234"),
    )
    def test_cli_creates_address_in_use(self, mock_convert):
        runner = CliRunner()
        address_create_output = runner.invoke(cli.main, input="1234,4321").output
        output_re = re.compile(
            r"Following addressed are in use: 1234. "
            "Please provide only new and unused addresses."
        )
        assert output_re.search(address_create_output) is not None
