import copy
import logging
import traceback

from extractor.common.services.IndParser import IndParser
from extractor.common.usecases.base import BaseUseCase
from ..controllers.deliveryaddress_controller import DeliveryAddressParserController
from extractor.ocr_utils import is_hybrid_order

logger = logging.getLogger("parser.delivery_address")

DIRECTION_HASHTAG_REFS = ["#dir", "#direccion", "#dirección"]


class DeliveryAddressParserUseCase(BaseUseCase):
    def __init__(self, config: dict, input_data: dict):
        """Initialization of parameters

        Args:
          config: dict with configuration
          input_doc: dict with the parser input format

        """

        super().__init__()
        self.config = config
        self.input_data = input_data
        self.result = None

    def execute(self):
        """Parses the delivery address indicators after they are tagged

        This parser generates annotations of type note that will be included in the output

        Leaves in result a Json with the same format as input with the result including the input and the parser annotations

        """
        try:
            input_data_copy = copy.deepcopy(self.input_data)
            deliveryaddress_controller = DeliveryAddressParserController(
                input_data_copy
            )
            deliveryaddress_controller.process_input()

            ind_tagged_in_email = False
            for idx, _datum in enumerate(input_data_copy["data"]):
                page = _datum["page"]

                lines_list = None
                if _datum.get("is_email_file", False) or is_hybrid_order(_datum):

                    lines_list = self.get_elements_with_given_body_tag(
                        _datum["elements"], DIRECTION_HASHTAG_REFS
                    )
                    if lines_list:
                        ind_tagged_in_email = True
                    deliveryaddressind_tagged = lines_list

                if not lines_list and not ind_tagged_in_email:
                    deliveryaddressind_tagged = (
                        deliveryaddress_controller.get_elements_with_a_given_tag(
                            _datum["elements"], "DELIVERYIND"
                        )
                    )

                address1_elements = (
                    deliveryaddress_controller.get_elements_with_a_given_tag(
                        _datum["elements"], "ADDRESS1"
                    )
                )
                addressx_elements = (
                    deliveryaddress_controller.get_elements_with_a_given_tag(
                        _datum["elements"], "ADDRESSX"
                    )
                )
                address_elements = address1_elements + addressx_elements
                address_annotations = (
                    deliveryaddress_controller.get_page_label_annotations(
                        input_data_copy["annotations"], page, "address"
                    )
                )
                deliveryaddress_list = IndParser.extract_labels_based_on_context(
                    deliveryaddressind_tagged,
                    address_annotations,
                    address_elements,
                    self.config["max_distance_score"],
                )

                deliveryaddress_list = IndParser.extract_position_element(
                    deliveryaddressind_tagged, deliveryaddress_list, address_elements
                )

                self.result = deliveryaddress_controller.process_result(
                    deliveryaddress_list
                )
        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error("{} - {}".format(e.__class__.__name__, e))
            logger.warning("Execution continues without deliveryaddress parsing")
            self.result = copy.deepcopy(self.input_data)
        return self.result

    def get_elements_with_given_body_tag(
        self, elem_list: list[dict], key_tags: list
    ) -> list[int]:

        element_list = []

        for _elem in elem_list:
            text = _elem["text"].replace("# ", "#")
            if any([key_tag.lower() in text.lower() for key_tag in key_tags]):
                _elem["body_client_tag"] = True
                element_list.append(_elem)

        return element_list

