from abc import ABC

from extractor.common.controllers.base import BaseController
from extractor.parsers.deliverydate_parser.controllers.custom_exceptions import (
    DeliveryDateParserError,
)
import copy


class DeliveryAddressParserController(BaseController, ABC):
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
            raise DeliveryAddressParserController("Annotations not found")

        elif "address" not in self.input_doc["annotations"]:
            raise DeliveryAddressParserController(
                "Delivery Address parser should be executed after Address parser"
            )
        for _datum in self.input_doc["data"]:
            if "elements" not in _datum or "lines" not in _datum:
                raise DeliveryAddressParserController(
                    "Every document should contain lines and elements"
                )

    def process_result(self, deliv_address_elements: list[dict]) -> list[dict]:

        if "annotations" not in self.result_doc:
            self.result_doc["annotations"] = {}
        if "delivery_address" not in self.result_doc["annotations"]:
            self.result_doc["annotations"]["delivery_address"] = []

        if len(deliv_address_elements) > 0:
            self.result_doc["annotations"]["delivery_address"] += deliv_address_elements

        return self.result_doc
