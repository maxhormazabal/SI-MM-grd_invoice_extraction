import logging

logger = logging.getLogger("parser.currency")


class CurrencyParserError(Exception):
    """Base class of the exception in this module"""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
