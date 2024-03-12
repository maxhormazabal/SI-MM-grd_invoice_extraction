from abc import ABC

from extractor.common.controllers.base import BaseController
from extractor.parsers.payment_parser.controllers.custom_exceptions import (
    PaymentNoteParserError,
)
import copy


class PaymentParserController(BaseController, ABC):
    def __init__(self, input_doc: dict):
        """Initialization of parameters

        Args:
          input_doc: dict with the parser input formats

        """

        super().__init__()
        self.input_doc = input_doc
        self.result_doc = copy.deepcopy(input_doc)

    def process_input(self):

        payind_list = list()
        paynote_list = list()

        if "annotations" not in self.input_doc:
            raise PaymentNoteParserError("Annotations not found")

        for _datum in self.input_doc["data"]:
            if "elements" not in _datum or "lines" not in _datum:
                raise PaymentNoteParserError(
                    "Every document should contain lines and elements"
                )
            payind_list += self.get_elements_with_a_given_tag(
                _datum["elements"], "PAYMENT_IND"
            )
            paynote_list += self.get_elements_with_a_given_tag(
                _datum["elements"], "PAYMENT_NOTE"
            )

        return payind_list, paynote_list

    def process_result(self, payment_elements: list[dict]) -> list[dict]:

        if "annotations" not in self.result_doc:
            self.result_doc["annotations"] = {}
        if "payment_note" not in self.result_doc["annotations"]:
            self.result_doc["annotations"]["payment_note"] = []

        if len(payment_elements) > 0:
            for elem in payment_elements:
                elem["text"] = elem["text"].strip().replace("\n", " ")
            self.result_doc["annotations"]["payment_note"] += payment_elements

        return self.result_doc
