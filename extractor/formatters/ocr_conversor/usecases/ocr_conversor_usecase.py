import os
import sys

# para ejecutar con pycharm-eliminar si da problemas
# sys.path.append(os.path.abspath("..."))


from extractor.common.usecases.base import BaseUseCase
from ..services.ocr_conversor import parse_ocr_content


class OCRConversorUseCase(BaseUseCase):
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

    def execute(self, page_widhts, page_heights):
        """Translates an OCR document to a parsers format

        This parser generates annotations of type product that will be included in the output

        Leaves in result a Json with the same format as input with the result including the input and the parser annotations

        """

        self.result = parse_ocr_content(
            self.config, self.input_doc, page_widhts, page_heights
        )
        return self.result
