import copy
import logging

from extractor.common.services.IndParser import IndParser
from extractor.common.usecases.base import BaseUseCase
from ..controllers.deliverydate_controller import DeliveryDateParserController

logger = logging.getLogger("parser.delivery_date")


class DeliveryDateParserUseCase(BaseUseCase):
    def __init__(self, config: dict, input_data: dict):
        """Initialization of parameters

        Args:
          input_doc: dict with the parser input formats

        Result:
            result: a dict with original text and dates

        """

        super().__init__()
        self.config = config
        self.input_data = input_data
        self.result = copy.deepcopy(input_data)

    def execute(self):
        """Parses the dates after they are tagged

        This parser generates annotations of type date that will be included in the output

        Leaves in result a Json with the same format as input with the result including the input and the parser annotations

        """
        try:
            input_data_copy = copy.deepcopy(self.input_data)
            deliverydate_controller = DeliveryDateParserController(input_data_copy)
            deliverydate_controller.process_input()

            for idx, _datum in enumerate(input_data_copy["data"]):
                page = _datum["page"]
                # source = _datum["source"]

                deliverydatesind_tagged = (
                    deliverydate_controller.get_elements_with_a_given_tag(
                        _datum["elements"], "DELIVERYDATEIND"
                    )
                )
                date_elements = deliverydate_controller.get_elements_with_a_given_tag(
                    _datum["elements"], "DATE"
                )
                dates_annotations = deliverydate_controller.get_page_label_annotations(
                    input_data_copy["annotations"], page, "date"
                )
                deliverydates_list = IndParser.extract_labels_based_on_context(
                    deliverydatesind_tagged,
                    dates_annotations,
                    date_elements,
                    self.config["max_distance_score"],
                )

                deliverydates_list = IndParser.extract_position_element(
                    deliverydatesind_tagged, deliverydates_list, date_elements
                )

                self.result = deliverydate_controller.process_result(deliverydates_list)
        except Exception as e:
            logger.error("{} - {}".format(e.__class__.__name__, e))
            logger.warning("Execution continues without deliverydate parsing")
            self.result = copy.deepcopy(self.input_data)
        return self.result
