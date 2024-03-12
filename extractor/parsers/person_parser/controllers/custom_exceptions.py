import logging

logger = logging.getLogger("parser.person")

# esto hay que ELIMINARLO, por ahora lo dejo por coincidir con el resto


class PersonParserError(Exception):
    """Base class of the exception in this module"""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
