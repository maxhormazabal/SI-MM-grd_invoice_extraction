from abc import ABC

from extractor.common.usecases.base import BaseUseCase

import logging

logger = logging.getLogger(__name__)


class OrderExtractorUseCase(BaseUseCase, ABC):
    def __init__(self, config: dict, input_doc: dict):
        """Initialization of parameters

        Args:
          config: dict with configuration
          input_doc: dict with the parser input format

        """

        super().__init__()
        self.config = config
        self.input_doc = input_doc
