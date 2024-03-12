from abc import ABC

from extractor.common.controllers.base import BaseController
from extractor.parsers.deliverydate_parser.controllers.custom_exceptions import (
    DeliveryDateParserError,
)
import copy


class DeliveryDateParserController(BaseController, ABC):
    def __init__(self, input_doc: dict):
        """Initialization of parameters

        Args:
          input_doc: dict with the parser input formats

        """

        super().__init__()
        self.input_doc = input_doc
        self.result_doc = copy.deepcopy(input_doc)

    def process_input(self):

        if "annotations" not in self.input_doc:
            raise DeliveryDateParserError("Annotations not found")

        elif "date" not in self.input_doc["annotations"]:
            raise DeliveryDateParserError(
                "Date parser should be executed before deliverydate parser"
            )
        for _datum in self.input_doc["data"]:
            if "elements" not in _datum or "lines" not in _datum:
                raise DeliveryDateParserError(
                    "Every document should contain lines and elements"
                )

    def process_result(self, date_elements: list[dict]) -> list[dict]:

        if "annotations" not in self.result_doc:
            self.result_doc["annotations"] = {}
        if "deliverydate" not in self.result_doc["annotations"]:
            self.result_doc["annotations"]["deliverydate"] = []

        if len(date_elements) > 0:
            self.result_doc["annotations"]["deliverydate"] += date_elements
        return self.result_doc
