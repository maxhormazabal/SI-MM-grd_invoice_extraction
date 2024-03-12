import logging


logger = logging.getLogger("labeler.onnx")


class ONNXClassError(Exception):
    """Base class of the exceptions in this module"""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class ModelExecutionError(ONNXClassError):
    """It captures errors related to model execution"""

    def __str__(self):
        return f"Error during model execution -> {self.message}"


class ModelInitializationError(ONNXClassError):
    """It captures errors related to model initialization"""

    def __str__(self):
        return f"Error during model initialization -> {self.message}"


class DataError(ONNXClassError):
    """It captures errors related to bad input text"""

    def __str__(self):
        return f"Error in input data -> {self.message}"


class TokenizerError(ONNXClassError):
    """It captures errors related to data tokenization"""

    def __str__(self):
        return f"Error during tokenization -> {self.message}"
