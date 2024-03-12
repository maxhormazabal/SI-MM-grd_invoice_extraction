import logging
import traceback
from abc import ABC

from extractor.common.controllers.base import BaseController
from extractor.parsers.company_parser.controllers.custom_exceptions import (
    CompanyParserError,
)
import copy

logger = logging.getLogger("parser.company")

CLIENT_HASHTAG_REFS = ["#cliente", "#cli"]


class CompanyParserController(BaseController, ABC):
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
            raise CompanyParserError("Every document should contain lines and elements")

        # if data.get("is_email_file", False):
        lines_list = self.get_elements_with_given_body_tag(
            data["elements"], CLIENT_HASHTAG_REFS
        )
        if lines_list:
            return lines_list

        lines_list = self.get_elements_with_a_given_tag(data["elements"], "COMPANY")
        return lines_list

    def process_result(self, company_elements: list[dict]) -> dict:

        if "annotations" not in self.result_doc:
            self.result_doc["annotations"] = {}
        if "company" not in self.result_doc["annotations"]:
            self.result_doc["annotations"]["company"] = []

        if len(company_elements) > 0:
            self.result_doc["annotations"]["company"] += company_elements

        return self.result_doc

    def get_elements_with_given_body_tag(
        self, elem_list: list[dict], key_tags: list
    ) -> list[int]:
        element_list = []
        try:

            prev_is_tag = False
            for _elem in elem_list:
                text = _elem["text"].replace("# ", "#")
                if any([key_tag.lower() in text.lower() for key_tag in key_tags]):
                    txt = (
                        _elem.get("text")
                        .lower()
                        .replace("#", "")
                        .replace("cliente", "")
                        .replace("cli", "")
                        .replace("\n", "")
                        .strip()
                    )
                    letters = sum(c.isalpha() for c in txt)
                    if letters > 2:
                        _elem["body_client_tag"] = True
                        element_list.append(_elem)
                        prev_is_tag = False
                    else:
                        prev_is_tag = True
                elif "#" in _elem.get("text"):
                    prev_is_tag = False
                elif prev_is_tag:
                    letters = sum(c.isalpha() for c in _elem.get("text"))
                    if letters > 2:
                        _elem["body_client_tag"] = True
                        element_list.append(_elem)
                        prev_is_tag = False
        except Exception:
            logger.error(traceback.format_exc())

        return element_list
