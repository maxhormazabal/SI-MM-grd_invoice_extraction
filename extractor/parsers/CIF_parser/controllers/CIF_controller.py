import logging
from abc import ABC

from extractor.common.controllers.base import BaseController
from extractor.parsers.CIF_parser.controllers.custom_exceptions import (
    CIFParserError,
)
import copy

logger = logging.getLogger("parser.CIF")


class CIFController(BaseController, ABC):
    def __init__(self, input_doc: dict):
        """Initialization of parameters

        Args:
          input_doc: dict with the parser input formats

        """

        super().__init__()
        self.input_doc = input_doc
        self.result_doc = copy.deepcopy(input_doc)

    def process_input(self, data: dict) -> list[str]:

        if "elements" not in data or "lines" not in data:
            raise CIFParserError("Every document should contain lines and elements")

        return data["elements"]

    def process_result(self, cif_elements: list[dict]) -> list[dict]:

        if "annotations" not in self.result_doc:
            self.result_doc["annotations"] = {}
        if "cif" not in self.result_doc["annotations"]:
            self.result_doc["annotations"]["cif"] = []

        if len(cif_elements) > 0:
            self.result_doc["annotations"]["cif"] += cif_elements
        else:
            self.result_doc["annotations"]["cif"] = []

        return self.result_doc

    def format_cif_annotation(
        self, cif, source, page, elem_list, related_company, complete_element_text
    ):
        return {
            "text": cif,
            "source": source,
            "page": page,
            "elements": elem_list,
            "related_company": related_company,
            "complete_element_text": complete_element_text,
        }
