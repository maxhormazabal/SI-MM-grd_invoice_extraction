from abc import ABC

from extractor.ocr_utils import is_hybrid_order
from extractor.common.controllers.base import BaseController
from extractor.parsers.address_parser.controllers.custom_exceptions import (
    AddressParserError,
)
import copy


class AddressParserController(BaseController, ABC):
    def __init__(self, input_doc: dict):
        """Initialization of parameters

        Args:
          input_doc: dict with the parser input formats

        """

        super().__init__()
        self.input_doc = input_doc
        self.result_doc = copy.deepcopy(input_doc)

    def process_input(self, data: dict, is_last_page=False) -> list[str]:

        if "elements" not in data or "lines" not in data:
            raise AddressParserError("Every document should contain lines and elements")

        if data.get("is_email_file") or is_hybrid_order(data):
            data, address_ind = self.set_address_to_lines_with_ind_hashtag(data)

        if is_hybrid_order(data) and is_last_page:
            address_lines = self.get_elements_with_a_given_list_of_tags(
                data.get("elements"), ["ADDRESS1", "ADDRESSX"]
            )
            address_lines = [ad for ad in address_lines if "DELIVERYIND" in ad.get("labels")]
            return address_lines

        address_lines = self.get_elements_with_a_given_list_of_tags(
            data.get("elements"), ["ADDRESS1", "ADDRESSX"]
        )

        return address_lines

    def process_result(self, result_annotations_list, data_copy):

        if "annotations" not in data_copy:
            data_copy["annotations"] = {}
        if "address" not in data_copy:
            data_copy["annotations"]["address"] = []

        if len(result_annotations_list) > 0:
            data_copy["annotations"]["address"] += result_annotations_list

        return data_copy

    def set_address_to_lines_with_ind_hashtag(self, data):
        address_ind = False
        for elem in data.get("elements"):
            if elem.get("text", "").lower().startswith("#dir"):
                address_ind = True
                if "ADDRESS1" not in elem.get("labels") or "ADDRESSX" not in elem.get(
                    "labels"
                ):
                    letters = sum(
                        c.isalpha()
                        for c in elem.get("text").lower().replace("#dir", "")
                    )
                    if letters > 3:
                        elem["labels"] += ["ADDRESS1"]
                if "DELIVERYIND" not in elem.get("labels"):
                    elem["labels"] += ["DELIVERYIND"]
                elem["body_client_tag"] = True

        return data, address_ind
