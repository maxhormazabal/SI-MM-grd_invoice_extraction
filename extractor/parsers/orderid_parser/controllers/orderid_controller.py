from abc import ABC

from extractor.common.controllers.base import BaseController
from extractor.parsers.orderid_parser.controllers.custom_exceptions import (
    OrderIDParserError,
)
import copy

REFERENCES_HASHTAG_REFS = ["#ref", "#reference"]


class OrderIDParserController(BaseController, ABC):
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
            raise OrderIDParserError("Annotations not found")

        for _datum in self.input_doc["data"]:
            if "elements" not in _datum or "lines" not in _datum:
                raise OrderIDParserError(
                    "Every document should contain lines and elements"
                )

    def process_result(self, orderid_elements: list[dict]) -> list[dict]:

        if "annotations" not in self.result_doc:
            self.result_doc["annotations"] = {}
        if "orderid" not in self.result_doc["annotations"]:
            self.result_doc["annotations"]["orderid"] = []

        if len(orderid_elements) > 0:
            self.result_doc["annotations"]["orderid"] += orderid_elements
        return self.result_doc

    def get_next_elements_of_orderind(
        self, elements, lines, orderind_tagged, orderid_elements
    ):
        already_got_elements = [elem.get("orig").get("id") for elem in orderid_elements]
        new_orderids = list()
        for orderind in orderind_tagged:
            if "ORDERID" in orderind.get("labels"):
                continue
            id_orderind = orderind.get("orig").get("id")

            # get the next element in the same line
            id_line = self.get_line_idx_with_a_given_elements(lines, [id_orderind])[0]
            line = lines[id_line]
            elems_line = [elem for elem in line.get("orig")]
            idx = None
            for i, elem in enumerate(elems_line):
                if elem.get("text") == orderind.get("text"):
                    idx = i
            if len(elems_line) > idx + 1:
                id_new_orderid = elems_line[idx + 1].get("id")
                if id_new_orderid in already_got_elements:
                    continue
                element_new = self._get_element_with_a_given_id(
                    elements, id_new_orderid
                )
                new_orderids.append(element_new)
                already_got_elements.append(id_new_orderid)

            # get the next element (could not be the same due to row_tol
            if id_orderind + 1 in already_got_elements:
                continue
            for element in elements:
                if element.get("orig").get("id") == id_orderind + 1:
                    if "DATE" not in element.get("labels"):
                        new_orderids.append(element)
                    break

        return new_orderids

    def get_orderid_elements_line_below(
        self, elements, lines, orderind_tagged, orderid_elements
    ):
        try:
            already_got_elements = [
                elem.get("orig").get("id") for elem in orderid_elements
            ]
            new_orderids = list()
            for orderind in orderind_tagged:
                if "ORDERID" in orderind.get("labels"):
                    continue
                id_element = orderind.get("orig").get("id")
                id_line = self.get_line_idx_with_a_given_elements(lines, [id_element])[
                    0
                ]
                line = lines[id_line]
                next_line = lines[id_line + 1]
                elems_line = [elem for elem in line.get("orig")]
                idx = None
                for i, elem in enumerate(elems_line):
                    if elem.get("text") == orderind.get("text"):
                        idx = i
                if idx is not None:
                    elems_next_line = [elem for elem in next_line.get("orig")]
                    id_new_orderid = elems_next_line[idx].get("id")
                    if id_new_orderid in already_got_elements:
                        continue
                    element_new = self._get_element_with_a_given_id(
                        elements, id_new_orderid
                    )
                    new_orderids.append(element_new)

            return new_orderids
        except:
            return list()

    def get_elements_with_given_body_tag(self, data: list[dict]) -> list[int]:
        element_list = []

        for page in data:

            for _elem in page.get("elements"):
                text = _elem["text"].replace("# ", "#")
                if any(
                    [
                        key_tag.lower() in text.lower()
                        for key_tag in REFERENCES_HASHTAG_REFS
                    ]
                ):
                    _elem["body_orderid_tag"] = True
                    element_list.append(_elem)

        return element_list

    def get_page_of_element_with_id(self, id_elem, data):
        for i, page in enumerate(data.get("data")):
            for elem_data in page.get("elements"):
                if id_elem == elem_data.get("orig").get("id"):
                    return i

        return 0
