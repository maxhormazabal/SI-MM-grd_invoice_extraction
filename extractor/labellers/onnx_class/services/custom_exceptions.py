import logging


logger = logging.getLogger("labeler.onnx")


class TagDocumentError(Exception):
    """Base class of the exception in this module"""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
