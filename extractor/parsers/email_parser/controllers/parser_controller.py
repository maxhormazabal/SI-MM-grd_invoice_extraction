from abc import ABC

from extractor.common.controllers.base import BaseController
from extractor.parsers.email_parser.controllers.custom_exceptions import (
    EmailParserError,
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
            raise EmailParserError("Every document should contain lines and elements")

        lines_list = self.get_elements_with_a_given_tag(data["elements"], "EMAIL")
        return lines_list

    def process_result(self, email_elements: list[dict]) -> dict:

        if "annotations" not in self.result_doc:
            self.result_doc["annotations"] = {}
        if "email" not in self.result_doc["annotations"]:
            self.result_doc["annotations"]["email"] = []

        if len(email_elements) > 0:
            self.result_doc["annotations"]["email"] += email_elements
        return self.result_doc
