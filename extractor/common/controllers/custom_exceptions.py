import logging


logger = logging.getLogger(__name__)

# esto hay que ELIMINARLO, por ahora lo dejo por coincidir con el resto


class DeliveryAddressDesambiguatorError(Exception):
    """Base class of the exception in this module"""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class ClientDesambiguatorError(Exception):
    """Base class of the exception in this module"""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class ProductDesambiguatorError(Exception):
    """Base class of the exception in this module"""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class ElasticDesambiguationError(Exception):
    """Base class of the exception in this module"""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
