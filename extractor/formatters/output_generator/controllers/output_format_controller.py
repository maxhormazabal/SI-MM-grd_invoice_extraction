import copy
import logging
from abc import ABC

from extractor.common.controllers.base import (
    BaseController,
)

logger = logging.getLogger("format.output")


class OutputFormatController(BaseController, ABC):
    def __init__(self, input_doc: dict, sourceFiles: list):
        """Initialization of parameters

        Args:
          input_doc: dict with the parser input formats

        """

        super().__init__()
        self.input_doc = input_doc
        self.result_doc = copy.deepcopy(input_doc)
        self.sourceFiles = sourceFiles if sourceFiles else []

    def process_input(self, input_doc: dict) -> list[str]:
        pass

    def process_result(self) -> list[str]:

        self.result_doc = self.get_template_document()

        return self.result_doc


    def get_template_document(self):
        data = dict()
        data["sourceFiles"] = self.sourceFiles if self.sourceFiles else []
        return data

    def get_template_product(self):
        data = dict()

        return data

    def get_empty_field_value(self):
        return {
            "text": None,
            "score": None,
            "validation": None,
            "raw": [
                {
                    "sourceFile": None,
                    "page": None,
                    "regionCoords": [
                        {"x": None, "y": None},
                        {"x": None, "y": None},
                        {"x": None, "y": None},
                        {"x": None, "y": None},
                    ],
                    "line": None,
                    "rawText": None,
                }
            ],
        }
