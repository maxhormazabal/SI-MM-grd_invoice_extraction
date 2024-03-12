import os
import sys
import logging

# para ejecutar con pycharm-eliminar si da problemas
# sys.path.append(os.path.abspath("..."))
import traceback

logger = logging.getLogger("labeler.onnx")

from extractor.common.usecases.base import BaseUseCase
from ..services.tagging_service import tag_elements


class TagDocumentsUseCase(BaseUseCase):
    def __init__(self, config: dict, input_doc: dict):
        """Initialization of parameters

        Args:
          config: dict with configuration
          input_doc: dict with the parser input format

        """

        super().__init__()
        self.config = config
        self.input_doc = input_doc
        self.result = None

    def execute(self):
        """Parses the products and their parameters after they are tagged

        This parser generates annotations labels for elements and lines of a document

        Leaves in result a Json with the same format as input with the result including the input and the parser annotations

        """
        try:
            self.result = tag_elements(self.config, self.input_doc)
        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error("Error with the label classification process")
            logger.error(e)
            return None

        return self.result
