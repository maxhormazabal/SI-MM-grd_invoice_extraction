from abc import ABC

from extractor.common.controllers.base import BaseController
from extractor.parsers.currency_parser.controllers.custom_exceptions import (
    CurrencyParserError,
)
import copy


class EmailParserController(BaseController, ABC):
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
            raise CurrencyParserError(
                "Every document should contain lines and elements"
            )

        lines_list = self.get_elements_with_a_given_tag(data["elements"], "CURRENCY")
        return lines_list

    def process_result(self, currency_elements: list[dict]) -> dict:

        if "annotations" not in self.result_doc:
            self.result_doc["annotations"] = {}
        if "currency" not in self.result_doc["annotations"]:
            self.result_doc["annotations"]["currency"] = []

        if len(currency_elements) > 0:
            self.result_doc["annotations"]["currency"] += currency_elements
        return self.result_doc
