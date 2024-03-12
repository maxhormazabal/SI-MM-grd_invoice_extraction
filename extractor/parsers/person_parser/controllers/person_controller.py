from abc import ABC

from extractor.common.controllers.base import BaseController
from extractor.parsers.person_parser.controllers.custom_exceptions import (
    PersonParserError,
)
import copy


class PersonParserController(BaseController, ABC):
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
            raise PersonParserError("Every document should contain lines and elements")

        lines_list = self.get_elements_with_a_given_tag(data["elements"], "PERSON")
        return lines_list

    def process_result(self, person_elements: list[dict]) -> list[dict]:

        if "annotations" not in self.result_doc:
            self.result_doc["annotations"] = {}
        if "persons" not in self.result_doc["annotations"]:
            self.result_doc["annotations"]["persons"] = []

        if len(person_elements) > 0:
            self.result_doc["annotations"]["persons"] += person_elements
        return self.result_doc
