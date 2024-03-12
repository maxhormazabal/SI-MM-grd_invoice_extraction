import copy
import logging
import re
import traceback

from extractor.ocr_utils import is_hybrid_order
from extractor.common.services.IndParser import IndParser
from extractor.common.usecases.base import BaseUseCase
from ..controllers.orderid_controller import OrderIDParserController
from ..services.orderid_service import (
    process_reference_text,
    replace_accents,
    remove_date_from_order_ref,
    is_orderid_format_element,
    clean_orderinds,
    get_orderid_of_body_tag,
)

from operator import itemgetter

logger = logging.getLogger("parser.order_id")


class OrderIDParserUseCase(BaseUseCase):
    def __init__(self, config: dict, input_data: dict):
        """Initialization of parameters

        Args:
          input_doc: dict with the parser input formats

        Result:
            result: a dict with original text and order ids

        """

        super().__init__()
        self.config = config
        self.input_data = input_data
        self.result = copy.deepcopy(input_data)
        self.client = None
        self.client_group = None
        self.country = None

    def execute(self):
        """Parses the order ids after they are tagged

        This parser generates annotations of type orderid that will be included in the output

        Leaves in result a Json with the same format as input with the result including the input and the parser annotations

        """
        try:
            input_data_copy = copy.deepcopy(self.input_data)
            orderid_controller = OrderIDParserController(input_data_copy)
            orderid_controller.process_input()
            (
                self.client,
                self.client_group,
                self.country,
            ) = orderid_controller.get_desamibiguated_client_data()

            if input_data_copy.get("is_email_file", False) or is_hybrid_order(
                input_data_copy
            ):
                orderid_annotations = get_annotations_from_body_tags(
                    orderid_controller, input_data_copy
                )
                if orderid_annotations:
                    self.result = orderid_controller.process_result(orderid_annotations)
                    return self.result

            for idx, _datum in enumerate(input_data_copy["data"]):
                page = _datum["page"]
                source = _datum["source"]
                orderind_tagged = orderid_controller.get_elements_with_a_given_tag(
                    _datum["elements"], "ORDERIND"
                )

                """
                logger.debug(
                    " ** ORDERIND: "
                    + " || ".join([o.get("text") for o in orderind_tagged])
                )
                """

                orderind_tagged = clean_orderinds(
                    orderind_tagged, self.config.get("blacklist_orderind")
                )

                orderid_elements = orderid_controller.get_elements_with_a_given_tag(
                    _datum["elements"], "ORDERID"
                )

                orderid_elements = self.find_contiguous_not_tagged_orderids(
                    orderind_tagged, orderid_elements, _datum, orderid_controller
                )


                orderid_annotations = (
                    orderid_controller.transform_element_to_annotation(
                        orderid_elements, page, source
                    )
                )

                orderid_list = IndParser.extract_labels_based_on_context(
                    orderind_tagged,
                    orderid_annotations,
                    orderid_elements,
                    self.config["max_distance_score"],
                )
                orderid_list = remove_date_from_order_ref(
                    orderid_list,
                    orderind_tagged,
                    _datum.get("elements", []),
                    self.client,
                )

                orderid_list = IndParser.extract_position_element(
                    orderind_tagged, orderid_list, orderid_elements
                )

                orderid_list = sorted(
                    orderid_list, key=itemgetter("score"), reverse=True
                )

                orderid_list = process_reference_text(
                    orderid_list, self.config.get("remove_words_order_ref")
                )

                self.result = orderid_controller.process_result(orderid_list)
        except Exception as e:
            logger.debug(traceback.format_exc())
            logger.error("{} - {}".format(e.__class__.__name__, e))
            logger.warning("Execution continues without orderid parsing")
            self.result = copy.deepcopy(self.input_data)
        return self.result

    def find_contiguous_not_tagged_orderids(
        self, orderind_tagged, orderid_elements, datum, controller
    ):
        try:
            # add the element in the same position in the line below (assuming table)
            below_orderid_elements = controller.get_orderid_elements_line_below(
                datum["elements"], datum["lines"], orderind_tagged, orderid_elements
            )

            # add the next element to the indicator in case is not tagged
            next_orderind_elements = controller.get_next_elements_of_orderind(
                datum["elements"],
                datum["lines"],
                orderind_tagged,
                orderid_elements + below_orderid_elements,
            )
            orderid_elements += [
                orderid
                for orderid in next_orderind_elements + below_orderid_elements
                if is_orderid_format_element(orderid, self.client, self.client_group)
            ]
        except Exception as e:
            logger.debug(traceback.format_exc())
            logger.error("{} - {}".format(e.__class__.__name__, e))
            logger.warning("Error in find_contiguous_not_tagged_orderids")

        return orderid_elements


def get_annotations_from_body_tags(orderid_controller, input_data_copy):
    orderid_list = orderid_controller.get_elements_with_given_body_tag(
        input_data_copy["data"]
    )

    if orderid_list:
        if len(orderid_list) != 1:
            logger.warning("There are more than one #ref indicator!")
        orderid_list_text, id_list = get_orderid_of_body_tag(
            orderid_list[0], input_data_copy
        )
        orderid_list[0]["text"] = orderid_list_text[0]
        page = orderid_controller.get_page_of_element_with_id(
            id_list[0], input_data_copy
        )
        orderid_annotations = orderid_controller.transform_element_to_annotation(
            orderid_list,
            page,
            input_data_copy.get("data")[0].get("source"),
        )
        orderid_annotations[0]["score"] = 1
        return orderid_annotations

    return []
