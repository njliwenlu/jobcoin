class WithdrawalAddressInUseException(Exception):
    def __init__(self, addresses):
        message = f"Following addressed are in use: {addresses}. Please provide only new and unused addresses."
        super().__init__(message)


class InvalidWithdrawalAddressException(Exception):
    def __init__(self):
        message = (
            "Empty addresses found, please provide comma-separated list of addresses."
        )
        super().__init__(message)


class CheckAddressInUseException(Exception):
    def __init__(self, response_text):
        message = f"Unable to check if input addresses are already in use. Please try again. Request response: {response_text}"
        super().__init__(message)
