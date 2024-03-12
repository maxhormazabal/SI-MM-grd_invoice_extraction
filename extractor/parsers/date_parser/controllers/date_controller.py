from abc import ABC

from extractor.ocr_utils import is_hybrid_order
from extractor.common.controllers.base import BaseController
from extractor.parsers.date_parser.controllers.custom_exceptions import DateParserError
import datetime
import re
import copy

DATE_HASHTAG_REFS = ["#fecha", "#fec"]


class DateParserController(BaseController, ABC):
    def __init__(self, input_doc: dict):
        """Initialization of parameters

        Args:
          input_doc: dict with the parser input formats

        """

        super().__init__()
        self.input_doc = input_doc
        self.result_doc = input_doc  # copy.deepcopy(input_doc)

    def process_input(self, data: dict) -> list[str]:

        if "elements" not in data or "lines" not in data:
            raise DateParserError("Every document should contain lines and elements")
        lines_list = []

        if data.get("is_email_file", False) or is_hybrid_order(data):
            date_annotations = get_elements_with_given_body_tag(data)
            for date in date_annotations:
                if "DELIVERYDATEIND" not in date["labels"]:
                    date["labels"] = date["labels"] + ["DELIVERYDATEIND"]
                if "DATEIND" in date["labels"]:
                    date["labels"].remove("DATEIND")
            if date_annotations:
                lines_list += date_annotations

        lines_list += self.filter_no_valid_dates(
            self.get_elements_with_a_given_tag(data["elements"], "DATE")
        )

        # remove duplicates
        lines_list = [
            i for n, i in enumerate(lines_list) if i not in lines_list[n + 1 :]
        ]

        return lines_list

    def filter_no_valid_dates(self, date_elements_list: list):
        date_filtered_list = []

        # actual year
        actual_year = datetime.datetime.now().year

        date_filtered_list = [
            date
            for date in date_elements_list
            if not any(
                [
                    (int(year) > (actual_year + 2) or int(year) < (actual_year - 6))
                    for year in re.findall(
                        r"(?:(?<!\d)(?:18|19|20)[0-9]{2})", date["text"]
                    )
                ]
            )
        ]

        return date_filtered_list

    def process_result(self, elements: list[dict], field: str) -> list[dict]:

        if "annotations" not in self.result_doc:
            self.result_doc["annotations"] = {}
        self.result_doc["annotations"][field] = []

        if len(elements) > 0:
            self.result_doc["annotations"][field] += elements

        return self.result_doc


def get_elements_with_given_body_tag(data: list[dict]) -> list[int]:
    element_list = []

    for _elem in data.get("elements"):
        text = _elem["text"].replace("# ", "#")
        if any([key_tag.lower() in text.lower() for key_tag in DATE_HASHTAG_REFS]):
            _elem["body_date_tag"] = True
            element_list.append(_elem)

    return element_list
